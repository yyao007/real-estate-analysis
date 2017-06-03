# -*- coding: utf-8 -*-
import scrapy
from BiggerPockets.items import postItem, userItem
from scrapy.utils.project import get_project_settings
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import json

class ForumSpider(scrapy.Spider):
    name = "forum"
    allowed_domains = ["biggerpockets.com"]
    # Starting from page 1 to 1899. BiggerPockets has around 1860 pages of forums
    start_urls = ['https://www.biggerpockets.com/forums']+['https://www.biggerpockets.com/forums/?page=' + str(i) for i in range(1,500)]
    # start_urls = ['https://www.biggerpockets.com/forums']
    _stop_following_pages = False

    def __init__(self):
        self.homeDB = None
        self.users = set()
        self.settings = get_project_settings()

    def start_requests(self):
        self._last_crawl_time = self.homeDB.get_last_crawl_time()
        # start from a specified date
        if not self.settings.get('SINCE_LAST_CRAWL_TIME'):
            t = self.settings.get('LAST_TIME')
            self._last_crawl_time = datetime.strptime(t, '%Y-%m-%d %H:%M:%S')

        for url in self.start_urls:
            if self._stop_following_pages:
                self.logger.info('Hit the last time crawled page, stop following pages: {}'.format(url))
                break
            else:
                yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        discussions = response.xpath('//tbody/tr')
        if not discussions:
            print 'No forums, ignoring the url...'
            return

        for discuss in discussions:
            # stop following pages if seeing the last time crawled page
            if self.isLastTime(discuss):
                self.logger.info('stop following pages {}'.format(response))
                self._stop_following_pages = True
                return

            dis = {}
            name = discuss.xpath('td[@class="discussion-name"]')
            URL = name.xpath('a[@data-requires-user-level="0"]/@href').extract()
            # Skip private topic
            if not URL:
                continue
            dis['URL'] = response.urljoin(URL[0])
            dis['title'] = name.xpath('a/text()').extract()[0]
            dis['categoryURL'] = response.urljoin(name.xpath('span/a/@href').extract()[0])
            dis['category'] = name.xpath('span/a/text()').extract()
            dis['disPage'] = response.url
            request = scrapy.Request(dis['URL'], callback=self.parse_posts, dont_filter=True)
            request.meta['dis'] = dis
            yield request

    def parse_posts(self, response):
        dis = response.meta['dis']
        replyTo = int(response.xpath('//input[@id="first_post_id"]/@value').extract()[0])
        posts = response.xpath('//div[@class="topic"]/article')
        replyid = dis.get('replyid', 0)
        for post in posts:
            # skip removed posts
            if not post.xpath('section'):
                replyid += 1
                continue
            item = postItem()
            item['replyid'] = replyid
            item['disPage'] = dis['disPage']
            item['URL'] = dis['URL']
            item['title'] = dis['title']
            item['categoryURL'] = dis['categoryURL']
            item['category'] = dis['category']
            item['replyTo'] = replyTo
            item['pid'] = int(post.xpath('@id').extract()[0][1:])
            posttime = post.xpath('section//div[@class="post-info"]/span/text()').extract()[0]
            postTime = self.getPostTime(posttime)
            item['postTime'] = postTime
            body = post.xpath('section//div[@class="body"]/p//text()').extract()
            body = ''.join([('' if '@' in body[i-1] or i==0 or '@' in body[i] else '\n') + body[i].strip() for i in range(len(body))])
            item['body'] = ''.join(body)
            user_url = post.xpath('aside/div[@class="author"]/a/@href').extract()[0]
            user_url = response.urljoin(user_url + '.json')
            request = scrapy.Request(user_url, callback=self.parse_users1, dont_filter=True)
            request.meta['item'] = item
            yield request
            replyid += 1

        nextPage = response.xpath('//a[@class="next-page"]/@href').extract()
        if nextPage:
            dis['replyid'] = replyid
            nextPage = response.urljoin(nextPage[0])
            request = scrapy.Request(nextPage, callback=self.parse_posts)
            request.meta['dis'] = dis
            yield request

    def parse_users1(self, response):
        pItem = response.meta['item']
        d = json.loads(response.text)['user']
        uid = str(d.get('id', ''))
        pItem['uid'] = uid
        # Ignore duplicate users
        if uid in self.users:
            yield pItem
            return

        item = userItem()
        item['disPage'] = pItem['disPage']
        item['uid'] = uid
        name = d.get('display_name', '').split()
        first, last = name if len(name) == 2 else [name[0], ''] if len(name) == 1 else [name[0], name[-1]] if name else ['', '']
        item['firstName'] = first
        item['lastName'] = last
        item['source'] = response.url[:-5]
        item['numPosts'] = d.get('posts_count', 0)
        item['numVotes'] = d.get('votes_received', 0)
        item['numAwards'] = d.get('badgings_count', 0)
        types = {0: 'base', 1: 'plus', 2: 'pro'}
        account = d.get('account_type')
        item['account'] = types.get(account)
        item['city'] = d.get('city')
        item['state'] = d.get('state')
        t = d.get('created_on')
        if t:
            item['dateJoined'] = datetime.strptime(t, '%Y-%m-%dT%H:%M:%S-%f')

        item['seeking'] = d.get('currently_seeking')
        item['occupation'] = d.get('occupation')
        item['experience'] = d.get('real_estate_experience')
        item['goals'] = d.get('real_estate_goals')
        request = scrapy.Request(item['source'], callback=self.parse_users2, dont_filter=True)
        request.meta['item'] = item
        request.meta['pItem'] = pItem
        yield request

    def parse_users2(self, response):
        item = response.meta['item']
        connections = response.xpath('//ul[@class="connections"]/li/span/text()').extract()
        connections = [i for i in connections if i.strip()]
        item['colleagues'] = int(filter(unicode.isdigit, connections[0]))
        item['followers'] = int(filter(unicode.isdigit, connections[1]))
        item['following'] = int(filter(unicode.isdigit, connections[2]))
        # return userItem first to meet the foreign key constraint
        self.users.add(item['uid'])
        yield item
        yield response.meta['pItem']

    def isLastTime(self, dis):
        last_activity = dis.xpath('td[@class="last-activity"]/text()').extract()
        if last_activity:
            last_activity[0] += ' ago'
            new_post_time = self.getPostTime(last_activity[0])
            if new_post_time < self._last_crawl_time:
                return True

        return False


    def getPostTime(self, posttime):
        curr = datetime.now()
        t = posttime.split()
        postTime = None
        td = t[-3]
        # replied less than a minute ago
        if td == 'a':
            td = 0
        else:
            td = int(td)
        if t[-2] in 'seconds':
            postTime = curr - timedelta(seconds=td)
        elif t[-2] in 'minutes':
            postTime = curr - timedelta(minutes=td)
        elif t[-2] in 'hours':
            postTime = curr - timedelta(hours=td)
        elif t[-2] in 'days':
            postTime = curr - timedelta(days=td)
        elif t[-2] in 'months':
            postTime = curr - relativedelta(months=td)
        elif t[-2] in 'years':
            postTime = curr - relativedelta(years=td)
        return postTime




