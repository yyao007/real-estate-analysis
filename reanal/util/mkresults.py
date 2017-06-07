from db import *
from datetime import datetime, timedelta
from PIL import Image
import numpy as np
import wordcloud as wc
import fnmatch
import os

directory = os.path.dirname(__file__)

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
		
def key_phrases():
	year = datetime(year=2016, month=1, day=1)
	start, end = year, year.replace(year=year.year+1)
	sites = ['BiggerPockets', 'activerain']
	locations = [('Los Angeles', 'CA'), ('San Francisco', 'CA'), ('Chicago', 'IL')]
	for l in locations:
		for site in sites:
			keyphrases = get_keyphrase(site, l[0], l[1], start, end)
			relpath = '../results/{}_{}_{}.txt'.format('_'.join(l[0].split()), site, year.strftime('%Y'))
			file = os.path.join(directory, relpath)
			print 'saving {}'.format(file)
			save_keyphrases(keyphrases, file)		

def word_cloud():
	words_dir = os.path.join(directory, '../results/')

	for file in os.listdir(words_dir):
		if fnmatch.fnmatch(file, '*.txt'):
			print 'open {}'.format(file)
			text = open(os.path.join(words_dir, file)).read()
			mask_file = '../other/cloud_mask.png'
			mask = np.array(Image.open(os.path.join(directory, mask_file)))
			color_func = wc.random_color_func
			wordcloud = wc.WordCloud(background_color="white", max_words=100, mask=mask,
               scale=1.5, min_font_size=6, color_func=color_func, relative_scaling=0.6,
               margin=1)
			wordcloud.generate(text)
			pngfile = file.split('.')[0] + '.png'
			print 'save {}'.format(pngfile)
			wordcloud.to_file(os.path.join(words_dir, pngfile))


if __name__ == '__main__':
	# key_phrases()
	word_cloud()






