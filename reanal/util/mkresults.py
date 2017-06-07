from db import *
from datetime import datetime, timedelta
import os

def get_keyphrase(site, city, state, start, end):
	db = DB()
	session = db.get_session()
	results = session.query(Keyphrase).filter(Keyphrase.site==site).\
		filter(Keyphrase.city==city).filter(Keyphrase.state==state).\
		filter(Keyphrase.postTime.between(start, end)).\
		order_by(Keyphrase.postTime)

	keyphrases = []
	for k in results:
		keyphrases.append(k.key_phrase)

	return keyphrases

def save_keyphrases(keyphrases, file):
	with open(file, 'w') as f:
		for k in keyphrases:
			f.write(k + '\n')
	f.close()
				

if __name__ == '__main__':
	year = datetime(year=2016, month=1, day=1)
	start, end = year, year.replace(year=year.year+1)
	sites = ['BiggerPockets', 'activerain']
	locations = [('Los Angeles', 'CA'), ('San Francisco', 'CA'), ('Chicago', 'IL')]
	for l in locations:
		for site in sites:
			keyphrases = get_keyphrase(site, l[0], l[1], start, end)
			directory = os.path.dirname(__file__)
			relpath = '../results/{}_{}_{}.txt'.format('_'.join(l[0].split()), site, year.strftime('%Y'))
			file = os.path.join(directory, relpath)
			print 'saving {}'.format(file)
			save_keyphrases(keyphrases, file)






