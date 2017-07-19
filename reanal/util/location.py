# -*- coding: utf-8 -*-

from db import *
from corenlp import StanfordCoreNLPPLUS
from sqlalchemy import distinct, func
from main import merge_locations, to_dict
from convert import Convert
from nltk import word_tokenize
from multiprocessing.dummy import Pool as ThreadPool
from multiprocessing import Process, Lock
import os
import sys
import json
import requests
from datetime import datetime

'''
  Use Stanford Named Entity Recognizer to identify location in each post.
  Initializing nltk.tag.StanfordNERTagger:
    export STANFORDTOOLSDIR=$HOME
    export CLASSPATH=$STANFORDTOOLSDIR/stanford-ner-2016-10-31/stanford-ner.jar
    export STANFORD_MODELS=$STANFORDTOOLSDIR/stanford-ner-2016-10-31/classifiers

  Alternative:
    pip install stanfordcorenlp (much faster)
'''
lock = Lock()

def filter_func(w):
    return len(w) < 2 or bool(re.search(r'[\d\@\.]|__', w))

class Location(object):
    def __init__(self):
        self.db = DB()
        self.session = self.db.get_session()
        self.new_session = self.db.new_session()
        # self.st = StanfordCoreNLP('/home/yyao009/stanford-corenlp-full-2016-10-31/')
        self.st = StanfordCoreNLPPLUS('http://localhost')
        # path = os.path.dirname(__file__)
        # file = os.path.join(path, '../data/abbr.txt')
        self.convert = Convert()
        self.pool = ThreadPool(24)

    def update_post(self, location):
        post, loc = location
        d = {'city': loc[0], 'state': loc[1]}
        r = self.session.query(Posts).filter(Posts.URL==post.URL).\
            filter(Posts.replyid==post.replyid).update(d)
        self.session.commit()
        # self.session.remove()

    def estimate_location(self, text, orig_location):
        ner = self.st.ner(text.encode('utf-8'))
        entities = to_dict(ner, text)
        loc = merge_locations(entities['LOCATION'], text)
        loc_dict = {x.encode("utf8"):loc.count(x) for x in loc}
        city = state = ''
        # default set location to empty tuple
        location = ()
        # handle multiple locations
        if len(loc_dict) > 1:
            # select the most frequent location
            locations = sorted(loc_dict, key=lambda k: loc_dict[k], reverse=True)
            for l in locations:
                # check if l is a state
                abbr = self.convert.abbreviate(l)
                # Only need to do further condition checking if all the
                # locations appear same times.
                if not abbr and not city:
                    city = ' '.join(i[0].upper()+i[1:] for i in l.strip().lower().split())
                elif not state:
                    state = abbr

            if not (city and state):
                if city:
                    # with lock:
                    states = [s.state for s in self.new_session.query(Cities).filter(Cities.city==city)]
                    state = states[0] if len(states) == 1 else orig_location[1]
                else:
                    city = orig_location[0].strip().lower()
                    city = ' '.join(i[0].upper()+i[1:] for i in city.split())
            location = (city, state)
        # handle one location
        elif len(loc_dict) == 1:
            l = loc_dict.keys()[0]
            abbr = self.convert.abbreviate(l)
            if abbr:
                state = abbr
                city = orig_location[0].strip().lower()
                city = ' '.join(i[0].upper()+i[1:] for i in city.split())
            else:
                # with lock:
                city = l
                states = [s.state for s in self.new_session.query(Cities).filter(Cities.city==city)]
                state = states[0] if len(states) == 1 else orig_location[1]
            location = (city, state)
        # check if it is a valid location
        if location:
            exists = self.new_session.query(Cities).filter(Cities.city==location[0]).\
                filter(Cities.state==location[1]).first()
            location = location if exists else (location[0], None)
            self.new_session.remove()

        return location

    def get_location(self, posts):
        '''
            Get location from a post
            posts is a (post, orig_location) tuple where
            orig_location is the location from starting post
        '''
        post, orig_location = posts
        tags, body, replyid = post.tags, post.body, post.replyid
        location = ()
        # 1. check location in post tags
        if tags:
            location = self.estimate_location(tags, orig_location)
        # 2. check location in post body
        if not location:
            location = self.estimate_location(body, orig_location)
        # 3. apply location from the starting post.
        if not location:
            location = orig_location

        # **** apply user's location if it's the starting post
        # if not location and replyid == 0:
        #     location = (user.city, user.state)

        return post, location

    def iter_posts(self):
        all_posts = self.session.query(Posts, Users).join(Users).\
            filter(func.length(Users.state)==2).filter(Posts.city==None).\
            group_by(Posts.URL, Posts.replyid)
        count = 0
        posts = []
        for post, user in all_posts:
            if count % 100:
                print 'Updated {} posts'.format(count)
            count += 1
            if post.replyid == 0:
                if posts:
                    yield posts
                posts = [(post, user)]
            else:
                posts.append((post, user))
        # yield the last set of posts
        if posts:
            yield posts

    def extract_location(self, url_obj):
        url = url_obj[0]
        posts = self.session.query(Posts, Users).join(Users).\
                filter(Posts.URL==url)
        print 'Processing {}'.format(url.encode('utf-8'))

        orig_post = posts.order_by(Posts.replyid)[0]
        city = orig_post.Users.city.encode('utf-8') if orig_post.Users.city else ''
        state = orig_post.Users.state.encode('utf-8') if orig_post.Users.state else ''
        orig_location = city, state

        # updating_posts = [(post.Posts, orig_location) for post in posts.filter(Posts.city==None)]
        # locations = self.pool.map(self.get_location, updating_posts)
        for post in posts.filter(Posts.city==None):
            updating_post = post.Posts, orig_location
            location = self.get_location(updating_post)
            self.update_post(location)
        self.session.remove()

        # return locations


    def process_posts(self):
        print 'Extracting forums...',
        sys.stdout.flush()
        # url_count = self.session.query(func.count(distinct(Posts.URL))).filter(Posts.city==None).first()[0]
        # print 'total: {}'.format(url_count)

        urls = self.session.query(distinct(Posts.URL)).filter(Posts.city==None)
                # .yield_per(100).enable_eagerloads(False)

        # count = 0
        # for url in urls:
            # if count % 100 == 0:
            #     print 'Finished: {0:.2f}%'.format(float(count)/url_count * 100)
            # count += 1
            # locations = self.extract_location(url[0])
            # self.pool.map(self.update_post, locations)
            # for location in self.extract_location(url[0]):
            #     self.update_post(location)

        self.pool.map(self.extract_location, urls)


if __name__ == '__main__':
    loc = Location()

    start = datetime.now()
    loc.process_posts()
    end = datetime.now()
    print 'Total time for extracting location: {}'.format(end - start)
    # all_posts = loc.session.query(Posts, Users).yield_per(100).enable_eagerloads(False).\
    #             join(Users).yield_per(100).enable_eagerloads(False).\
    #             filter(func.length(Users.state)==2).filter(Posts.city==None).\
    #             order_by(Posts.URL, Posts.replyid)
    # pool = ThreadPool(8)
    # pool.map(loc.process_post, all_posts)













