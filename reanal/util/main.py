# -*- coding: utf-8 -*-
'''
	Modified on 06/01/2017, by Yuan Yao

	@author: Tianrui Yang
	
'''

from itertools import islice
from nltk.tag import StanfordNERTagger
from nltk import word_tokenize, sent_tokenize
from datetime import date, timedelta, datetime
from multiprocessing import Pool

import mysql.connector
import nltk
import os


def remove_non_ascii_1(text):
	return ''.join([i if ord(i) < 128 else ' ' for i in text])

def merge_locations(locs, text):
    idx = 0
    last_idx = len(locs) - 1
    #print last_idx
    merged = []
    while idx <= last_idx:
    	#print "idx:", idx
        loc = locs[idx]
        while idx < last_idx:
            gap, text, merge = gap_length(locs[idx], locs[idx+1], text)
            if gap < 3 and merge.startswith(' '):
                loc += merge
                idx += 1
            else:
                break
        merged.append(loc)
        idx += 1
    return merged

def merge_organizations(locs, text):
	idx = 0
	last_idx = len(locs) - 1
	merged = []
	while idx <= last_idx:
		#print "idx:", idx
		loc = locs[idx]
		while idx < last_idx:
			gap, text, merge = gap_length(locs[idx], locs[idx+1], text)
			if gap == -1:
				continue
			if gap < 3:
				loc += merge
				idx += 1
			else:
				break
		merged.append(loc)
		idx += 1
	return merged

def gap_length(word1, word2, text): 
	try:
		pos1, pos2 = text.index(word1), text.index(word2)
	except:
		return -1, '', ''
	pos1_e, pos2_e = pos1 + len(word1), pos2 + len(word2)
	gap = pos2 - pos1_e
	edited_text = chr(0)*pos1_e + text[pos1_e:]
	inter_text = text[pos1_e:pos2_e]
	return gap, edited_text, inter_text


def to_dict(tuples, text):
	"""
	This function convert the list of tuples(tagged text) to a dictionary
	"""
	dict = {'LOCATION':[], 'ORGANIZATION':[]}
	for t in tuples:
		if (dict.has_key(t[1]) and t[0] in text):
			dict[t[1]].append(t[0])
	return dict

def get_entities(text):
	for s in ('\f', '\n', '\r', '\t', '\v'): #strip whitespaces
		text = text.replace(s, ' ')

	st = StanfordNERTagger('english.all.3class.distsim.crf.ser.gz')
	st.tag(word_tokenize(text))
	
	entities = to_dict(st.tag(word_tokenize(text)), text)
	l = merge_locations(entities['LOCATION'], text)
	o = merge_organizations(entities['ORGANIZATION'], text)
	#l = entities['LOCATION']
	#o = entities['ORGANIZATION']
	return l, o

"""
Initialize all cities and states 
"""
cities, states = {}, []
cnx = mysql.connector.connect(user='tyang020', password='Ytr!2318', database='twitter')
curA = cnx.cursor(buffered=True)
query_cities = (
	"SELECT city, COUNT(*) FROM locationCache GROUP BY city")
query_states = (
	"SELECT state, state_code FROM locationCache GROUP BY state")
curA.execute(query_cities)
for (city, count) in curA:
	cities[city.lower()] = count

curA.execute(query_states)
for (state, state_code) in curA:
	states.append(state.lower())
	states.append(state_code.lower())


def prosses_article(row):
	id = row[0]
	filename = row[1]
	#print "processing %s" % id

	cnx = mysql.connector.connect(user='tyang020', password='Ytr!2318', database='twitter')
	curB = cnx.cursor(buffered=True)
	curC = cnx.cursor(buffered=True)

	query_coor_city = ("SELECT latitude, longitude, city, state, state_code FROM locationCache "
		"WHERE city = %s")
	query_coor_state = ("SELECT latitude, longitude, city, state, state_code FROM locationCache "
		"WHERE city = %s AND (state = %s OR state_code = %s)")
	insert_locs = ("INSERT INTO testlocations (id, latitude, longitude, location, freq) "
		"VALUES (%s, %s, %s, %s, %s)")
	insert_orgs = ("INSERT INTO testorganizations (id, organization, freq) "
		"VALUES (%s, %s, %s)")
		
	curB.execute("SELECT COUNT(DISTINCT id) FROM locations where id = %s", (id,))
	

	with open(filename, 'r') as f:
		text = f.read().decode("utf8")
		text = remove_non_ascii_1(text)
		print "processing file %s" % filename
		l, o = get_entities(text)
		l, o = [x.lower() for x in l], [x.lower() for x in o]
		loc_city, loc_state, organizations = {}, {}, {}
		if l != []:
			locations = {x.encode("utf8"):l.count(x) for x in l}
			for loc, count in locations.iteritems():
				if loc in cities:
					loc_city[loc] = count
				if loc in states:
					loc_state[loc] = count
		if o != []:
			organizations = {x.encode("utf8"):o.count(x) for x in o}

		visited_state = []
		for lc, lc_count in loc_city.iteritems():
			curB.execute(query_coor_city, (lc,))
			for (latitude, longitude, city, state, state_code) in curB:
				if cities[lc] == 1 or state in loc_state or state_code in loc_state:   #lc not in loc_state
					curC.execute(insert_locs, (id, latitude, longitude, city+', '+state, lc_count))
					visited_state.append(city.lower())
					visited_state.append(state.lower())
					visited_state.append(state_code.lower())
					break
		#insert states to table
		#print visited_state
		for ls, ls_count in loc_state.iteritems():
			if ls not in visited_state:
				curB.execute(query_coor_state, ('', ls, ls))
				for (latitude, longitude, city, state, state_code) in curB:
					curC.execute(insert_locs, (id, latitude, longitude, state, ls_count))
		for o, o_count in organizations.iteritems():
			curB.execute(insert_orgs, (id, o, o_count))
		cnx.commit()
		#return loc_city, loc_state, organizations


if __name__ == '__main__':
	#curr_date = date(2016, 11, 17)
	curr_date = (date.today()-timedelta(1)).isoformat()
	print "Start processing data %s at %s" % (curr_date, datetime.now())
	cnxmain = mysql.connector.connect(user='tyang020', password='Ytr!2318', database='twitter')
	
	cursor = cnxmain.cursor(buffered=True)

	query_article = (
		"SELECT id, article_location FROM tweet "
		"WHERE article_location IS NOT NULL "
		"AND DATE(creation_time) = %s")
	
	cursor.execute(query_article, (curr_date,))
	p = Pool()	
	p.map(prosses_article, cursor)
		
	cursor.close()
	cnxmain.close()
	print "Finished %s at %s" % (curr_date, datetime.now())
