# -*- coding: utf-8 -*-

import nltk
from nltk.collocations import *
from nltk import word_tokenize
from nltk.tokenize import RegexpTokenizer
from nltk.stem.snowball import SnowballStemmer
import sklearn
from sklearn.utils.fixes import bincount
from sklearn.feature_extraction.text import TfidfTransformer, CountVectorizer
from datetime import datetime, timedelta
from db import *
import numpy as np
import scipy.sparse as sp
import json
import calendar
import re
import sys
import os

seperator = '-' * 12

# source code: https://github.com/scikit-learn/scikit-learn/blob/14031f6/sklearn/feature_extraction/text.py
def _document_frequency(X):
    """Count the number of non-zero values for each feature in sparse X."""
    if sp.isspmatrix_csr(X):
        return bincount(X.indices, minlength=X.shape[1])
    else:
        return np.diff(sp.csc_matrix(X, copy=False).indptr)

def filter_func(w, stopwords=[]):
    return len(w) < 3 or w in stopwords or bool(re.search(r'[\d\@\.\']|__', w)) 

def iter_monthrange(start_date, end_date):
    start = datetime(start_date.year, start_date.month, 1)
    while start < end_date:
        day = calendar.monthrange(start.year, start.month)[1]
        yield (start, start.replace(day=day))
        start += timedelta(days=day)


class Feature_extraction:
    def __init__(self):
        database = DB()
        self.session = database.get_session() 

    def iter_monthrange(self, start_date, end_date):
        start = datetime(start_date.year, start_date.month, 1)
        while start < end_date:
            day = calendar.monthrange(start.year, start.month)[1]
            yield (start, start.replace(day=day))
            start += timedelta(days=day) 

    def tokenize(self, text):
        # stemmer = SnowballStemmer('english')
        tokenizer = RegexpTokenizer(r'[\w\.\@]+\b')
        # tokens = [stemmer.stem(t) for t in tokenizer.tokenize(text)]
        return [t.lower() for t in tokenizer.tokenize(text)]
        
    def filter_words(self, url):
        relpath = '../data/stop-word-list.txt'
        filename = os.path.join(os.path.dirname(__file__), relpath)
        with open(filename, 'r') as f:
            stopwords1 = [l.strip() for l in f]
        f.close()
        custom_stopwords = [u'com', u'www', u'www2', u'org', u'http', u'https', u'bigger', u'pockets', u'active', u'rain']
        url_like = '%' + url + '%'
        for firstName, lastName in self.session.query(Users.firstName, Users.lastName).filter(Users.source.like(url_like)):
            custom_stopwords.append(firstName.lower())
            custom_stopwords.append(lastName.lower())
        stopwords2 = nltk.corpus.stopwords.words('english')
        return set(stopwords1 + stopwords2 + custom_stopwords)
     
    def filter_func(self, w, stopwords=[]):
        # w1 = w.replace(',', '').replace('-', '')
        # ignore_chars = [u'.', u'@', u'--', u'__']
        # ignore_chars += range(10)
        return len(w) < 3 or w in stopwords or bool(re.search(r'[\d\@\.]|__', w)) # or any((c in w) for c in ignore_chars)

    def save_keyphrase(self, url, tfidf):
        count = 0.0
        total = len(tfidf.values())
        for k in tfidf:
            if count % 1000 == 0:
                print '{}%'.format(count/total * 100)
            count += 1
            
            for term in tfidf[k]:
                keyphrase = Keyphrase(
                    site=url, 
                    city=k[0], 
                    state=k[1], 
                    postTime=k[2], 
                    key_phrase=term[0], 
                    tfidf=term[1],
                )
                self.session.add(keyphrase)
            self.session.commit()

    def save_unigrams(self, url, phrases, unigrams):
        for i, v in enumerate(unigrams):
            unigram = Unigrams(site=url, key_phrase=phrases[i], _df=v)
            self.session.add(unigram)
            self.session.commit()

    def save_bigrams(self, url, phrases, fdist):
        for phrase in phrases:
            bigram = Bigrams(
                site=url, 
                key_phrase=' '.join(phrase[0]), 
                freq=fdist[phrase[0]],
                pmi=phrase[1],
            )
            self.session.add(bigram)
            self.session.commit()

    def collocations(self, url, freq_filter, n, text=None, filename=None):
        bigram_measures = nltk.collocations.BigramAssocMeasures()
        if text:
            tokens = self.tokenize(text)
        if filename:
            with open(filename, 'rU') as f:
                print 'reading file {}....'.format(filename)
                raw = f.read().decode('utf-8')
                print 'read done!'
                tokens = self.tokenize(raw)
                print 'tokenize done!'
            f.close()

        print 'Calculating colloacations...'
        finder = BigramCollocationFinder.from_words(tokens)
        finder.apply_freq_filter(freq_filter)
        stopwords = self.filter_words(url)
        finder.apply_word_filter(lambda w: self.filter_func(w, stopwords=stopwords))
        scored = sorted(finder.score_ngrams(bigram_measures.dice), key=lambda k: k[1], reverse=True)[:n]

        return scored, dict(finder.ngram_fd.viewitems())           
      
    def find_vocabulary(self, url, docs):
        hasVoc = self.session.query(Unigrams).filter(Unigrams.site==url).first()
        if not hasVoc:
            print 'Calculating vocabulary...',
            sys.stdout.flush()
            stopwords = self.filter_words(url)
            vec = CountVectorizer(tokenizer=self.tokenize, stop_words=stopwords, min_df=7, max_features=30000)
            vec.fit(docs.values())
            terms = vec.get_feature_names()
            vocabulary = [w for w in terms if not self.filter_func(w)]
            for k in self.session.query(Bigrams.key_phrase).filter(Bigrams.site == url):
                vocabulary.append(k[0])
            print 'Done!'
        else:
            print 'Extracting vocabulary from database...',
            sys.stdout.flush()
            vocabulary = [term[0] for term in self.session.query(Unigrams.key_phrase).filter(Unigrams.site==url)]
            print 'Done!'
        
        return vocabulary

    def tf_idf(self, url, docs, vocabulary):
        hasVoc = self.session.query(Unigrams).filter(Unigrams.site==url).first()
        
        count_vec = CountVectorizer(tokenizer=self.tokenize, ngram_range=(1,2), vocabulary=vocabulary)
        tfidf_vec = TfidfTransformer()
        countX = count_vec.fit_transform(docs.values())
        if not hasVoc:
            print 'Calculating document frequecy and save to database...',
            sys.stdout.flush()
            unigrams = _document_frequency(countX)
            self.save_unigrams(url, vocabulary, unigrams)
            print 'Done!'

        print 'Calculating tfidf for {} terms...'.format(len(vocabulary)),
        sys.stdout.flush()
        tfidf = tfidf_vec.fit_transform(countX).toarray()
        score_tfidf = [[(vocabulary[i], v) for i, v in enumerate(t) if v != 0] for t in tfidf]
        score_tfidf = [sorted(score, key=lambda k: k[1], reverse=True)[:50] for score in score_tfidf]
        # freqD = dict([[(vocabulary[i], v) for i, v in enumerate(c) if v != 0] for c in countX.toarray()])
        dict_tfidf = {}
        for i, v in enumerate(docs.keys()):
            dict_tfidf[v] = score_tfidf[i]
        print 'Done!'
        
        return dict_tfidf

    def extract_posts(self, url, start_date=None, end_date=None):
        url_like = '%' + url + '%'
        posts = self.session.query(Posts.body, Posts.city, Posts.state).\
                filter(Posts.URL.like(url_like)).filter(func.length(Posts.state)==2)
        # location = self.session.query(Users.city, Users.state).filter(Users.source.like(url_like)).filter(func.length(Users.state)==2).group_by(Users.city, Users.state)
        if not start_date:
            start_date = self.session.query(Posts.postTime).filter(Posts.URL.like(url_like)).order_by(Posts.postTime).first()
        if not end_date:
            end_date = self.session.query(Posts.postTime).filter(Posts.URL.like(url_like)).order_by(Posts.postTime.desc()).first()

        # To calculate tfidf of posts from each city, each month
        docs = {}
        for monthrange in self.iter_monthrange(start_date[0], end_date[0]):
            print '{}--{} :'.format(monthrange[0], monthrange[1]),
            sys.stdout.flush()
            count = 0
            monthlyPosts = posts.filter(Posts.postTime.between(monthrange[0], monthrange[1])).order_by(Posts.city, Posts.state)
            # monthlyPosts = posts.filter(Users.city=='CAMBRIDGE').filter(Users.state=='MA').filter(Posts.postTime.between(monthrange[0], monthrange[1]))
            # print monthlyPosts.statement.compile(self.engine)
            text = ''
            previous = ('', '')
            for post in monthlyPosts:
                city = post.city.strip().lower()
                city = ' '.join(i[0].upper()+i[1:] for i in city.split())
                state = post.state.strip().upper()
                if city == previous[0] and state == previous[1]:
                    text += post.body
                else: 
                    if text:
                        key = (previous[0], previous[1], monthrange[0])
                        docs[key] = text
                        count += 1
                    text = post.body
                    # print '{}=={}: {}, {}=={}: {}'.format(previous[0], city, previous[0]==city, previous[1], state, previous[1]==state)
                    previous = (city, state)
                    
            # To save the last city in the result query
            if text:
                key = (post.city, post.state, monthrange[0])
                docs[key] = text
                count += 1
            print 'total: {}'.format(count)

        return docs

    def find_key_phrase(self, url):
        '''
        
        Parameters
        ----------
        url: string {'BiggerPockets', 'activerain'}
            To seperate posts from two websites
        '''
        last_month = self.session.query(Keyphrase.postTime).filter(Keyphrase.site==url).order_by(Keyphrase.postTime.desc()).first()
        this_month = None
        if last_month:
            month = last_month[0].month + 1
            this_month = last_month[0].replace(month=month),
            print '{}Updating keyphrase table for {} from {}{}'.format(seperator, url, this_month[0], seperator)

        print '{}Extracting posts from {}{}'.format(seperator, url, seperator)
        # seperate posts from BiggerPockets and activerain
        docs = self.extract_posts(url, start_date=this_month)

        print '{}Calculating TFIDF for {}{}'.format(seperator, url, seperator)         
        print 'total docs: {}'.format(len(docs))
        vocabulary = self.find_vocabulary(url, docs)
        tfidf = self.tf_idf(url, docs, vocabulary)
        print '{}Save key phrases to database{}'.format(seperator, seperator) 
        self.save_keyphrase(url, tfidf)
        print 'Done!'

    def all_bigrams(self, url):
        print 'Calculating all bigrams...'
        relpath = '../data/'
        data_dir = os.path.join(os.path.dirname(__file__), relpath)
        filename =  data_dir + '{}_posts.txt'.format(url)
        bigrams, fdist = self.collocations(url, 6, 5000, filename=filename)
        print 'Done!'

        print 'Save to database...'
        self.save_bigrams(url, bigrams, fdist)
        print 'Done!'

    def save_to_file(self, url):
        relpath = '../data/'
        data_dir = os.path.join(os.path.dirname(__file__), relpath)
        filename = data_dir + '{}_posts.txt'.format(url)
        print 'Extracting all posts from {}...'.format(url),
        url_like = '%' + url + '%'
        posts = self.session.query(Posts.body).filter(Posts.URL.like(url_like))
        total = posts.count()
        print 'total: {}'.format(total)
        count = 0
        with open(filename, 'w') as f:
            for body in posts:
                if count % 5000 == 0:
                    print '{}%'.format(round(float(count)/total*100, 2))
                count += 1
                f.write(body[0].encode('utf-8'))
        f.close()
        print 'Done!'

    def start(self, job, site):
        if job == 'key':
            self.find_key_phrase(site)
        elif job == 'bigram':
            self.all_bigrams(site)
        elif job == 'save':
            self.save_to_file(site)
        
if __name__ == '__main__':
    if len(sys.argv) == 1:
        print 'Usage: python features.py key/bigram [BiggerPockets] [activerain]'
        exit()
    elif len(sys.argv) > 2:
        sites = sys.argv[2:]
    else:
        sites = ['BiggerPockets', 'activerain']
    
    job = sys.argv[1]
    for site in sites:
        start_time = datetime.now()
        feature = Feature_extraction()
        if job == 'key':
            feature.find_key_phrase(site)
        elif job == 'bigram':
            feature.all_bigrams(site)
        elif job == 'save':
            feature.save_to_file(site)
    
        end_time = datetime.now()
        print 'Total time for {}: {}'.format(site, end_time - start_time)


       