# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
    
class postItem(scrapy.Item):
    URL = scrapy.Field() # discussion URL
    title = scrapy.Field() # discussion title
    category = scrapy.Field() # discussion category
    categoryURL = scrapy.Field()
    replyid = scrapy.Field() # reply id based on the discussion URL
    pid = scrapy.Field() # post id
    uid = scrapy.Field() # user id
    replyTo = scrapy.Field() # This is the first post id of the discussion
    postTime = scrapy.Field() # precise to hour eg. 2017-02-11 19:00:00
    body = scrapy.Field()
    disPage = scrapy.Field()
    
    def __repr__(self):
        # only print out attr1 after exiting the Pipeline
        return repr({"pid": self["pid"], 'page': self["disPage"][-6:]})

class userItem(scrapy.Item):
    uid = scrapy.Field() # user id
    firstName = scrapy.Field()
    lastName = scrapy.Field()
    source = scrapy.Field() # URL of the user profile
    colleagues = scrapy.Field()
    followers = scrapy.Field()
    following = scrapy.Field()
    numPosts = scrapy.Field()
    numVotes = scrapy.Field()
    numAwards = scrapy.Field()
    account = scrapy.Field() # account type: base, plus, pro
    city = scrapy.Field()
    state = scrapy.Field()
    dateJoined = scrapy.Field() # creation date of the user account
    seeking = scrapy.Field() # currently seeking
    occupation = scrapy.Field()
    experience = scrapy.Field() # real estate experience
    goals = scrapy.Field() # real estate goals
    disPage = scrapy.Field()
    
    def __repr__(self):
        # only print out attr1 after exiting the Pipeline
        return repr([self['firstName'], self['lastName'], self["disPage"][-6:]])
    