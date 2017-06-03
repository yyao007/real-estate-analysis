# -*- coding: utf-8 -*-
import scrapy
from activerain.items import postItem, userItem
from datetime import datetime
from scrapy.selector import Selector
# from scrapy.utils.project import get_project_settings
import json

class BlogSpider(scrapy.Spider):
    name = "blog"
    allowed_domains = ["activerain.com"]

    def __init__(self):
        self.homeDB = None
        self.users = set()
        #self.settings = get_project_settings()

    def start_requests(self):
        self.since = self.homeDB.since()
        self.start_urls = ['http://activerain.com/bloghome?filter=&page=1&since={0}'.format(self.since)]
        #self.start_urls = ['http://activerain.com/bloghome?filter=&page=29620&since={0}'.format(self.since)]
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse)


    def parse(self, response):
        last_page = response.xpath('//div[@class="pagination"]/a[@rel="nofollow"]/text()').extract()
        if last_page:
            self.last_page = int(last_page[-1])
        curr = response.url.split('&')[1].split('=')[-1]
        request = scrapy.Request(response.url, callback=self.parse_pages, dont_filter=True)
        request.meta['curr_page'] = int(curr)
        yield request

    def parse_pages(self, response):
        blogs = response.xpath('//div[@class="result-snippet"]')
        #nextPage = response.xpath('//a[@class="next_page"]/@href').extract()
        for blog in blogs:
            URL = blog.xpath('@data-url').extract()
            if not URL:
                continue
            b = {}
            b['URL'] = URL[0]
            b['blogid'] = blog.xpath('@data-id').extract()[0]
            b['title'] = blog.xpath('div/h2/a/text()').extract()[0]
            b['blogPage'] = response.url
            request = scrapy.Request(b['URL']+'?show_all=true', callback=self.parse_blogs)
            request.meta['blog'] = b
            yield request

        curr = response.meta['curr_page']
        if curr < self.last_page:
            next_page = 'http://activerain.com/bloghome?filter=&page={0}&since={1}'.format(int(curr)+1, self.since)
            request = scrapy.Request(next_page, callback=self.parse_pages)
            request.meta['curr_page'] = int(curr) + 1
            yield request

    def parse_blogs(self, response):
        count = 0
        # parse blog
        blog = response.meta['blog']
        user = user = response.xpath('//div[@class="author-details"]//a/@href').extract()[0]
        uid = user.split('/')[-1]
        if uid not in self.users:
            yield self.parse_author(response, blog['blogPage'])
            self.users.add(uid)
        item = postItem()
        item['URL'] = blog['URL']
        item['pid'] = int(blog['blogid'])
        item['title'] = blog['title']
        item['disPage'] = blog['blogPage']
        item['uid'] = uid
        # the replyid of the original blog is 0
        item['replyid'] = count
        t = response.xpath('//div[@class="blog-date"]/meta/@content').extract()[0]
        item['postTime'] = datetime.strptime(t, '%Y-%m-%dT%H:%M:%S')
        item['replyTo'] = 0
        body = response.xpath('//div[@itemprop="articleBody"]//text()').extract()
        # handle re-blog
        if not body:
            body = response.xpath('//div[contains(@class, "blog-content")]//text()').extract()
        item['body'] = ''.join(body).strip()
        likes = response.xpath('//div[@class="article-user-actions"]//div[@class="likes-count"]/text()').extract()
        likes = [i.strip() for i in likes if i.strip()]
        if likes:
            item['likes'] = int(filter(unicode.isdigit, likes[0]))

        category = response.xpath('//a[@class="tag"]')
        if category:
            item['category'] = category.xpath('text()').extract()[0]
            item['categoryURL'] = response.urljoin(category.xpath('@href').extract()[0])

        tags = response.xpath('//dd[@class="tag"]//text()').extract()
        if tags:
            item['tags'] = '\t'.join([i.strip() for i in tags if i.strip()])
        yield item

        # parse comments
        blog['replyid'] = {}
        comments = response.xpath('//div[@itemprop="comment"]')
        for c in comments:
            count += 1
            pid = c.xpath('@id').extract()[0]
            user = c.xpath('div[@class="comment-left-section"]/a/@href').extract()
            if not user:
                user = c.xpath('.//div[@class="comment-author"]/text()').extract()
                if not user:
                    continue
            uid = user[0].split('/')[-1]
            if uid not in self.users:
                yield self.parse_user(c, blog['blogPage'])
                self.users.add(uid)
            item = postItem()
            item['URL'] = blog['URL']
            item['pid'] =  int(pid)
            item['title'] = blog['title']
            item['disPage'] = blog['blogPage']
            item['uid'] = uid
            replyid = c.xpath('div//a[@class="comment-index"]/text()').extract()
            if replyid:
                item['replyid'] = int(filter(unicode.isdigit, replyid[0]))
            else:
                item['replyid'] = count
            blog['replyid'][pid] = item['replyid']
            blog['count'] = item['replyid']
            t = c.xpath('.//meta[@itemprop="datePublished"]/@content').extract()[0]
            item['postTime'] = datetime.strptime(t, '%Y-%m-%dT%H:%M:%S')
            item['replyTo'] = 0
            body = c.xpath('.//div[@itemprop="text"]//p//text()').extract()
            item['body'] = ''.join(body).strip()
            likes = c.xpath('.//div[@class="likes-count"]/text()').extract()
            if likes:
                item['likes'] = int(filter(unicode.isdigit, likes[0]))
            yield item

        # parse comment comments
        if comments:
            url = 'http://activerain.com/blog_entries/{0}/blog_comment_comments'.format(blog['blogid'])
            h = {
                'Accept': 'application/json,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'X-Requested-With': 'XMLHttpRequest',
            }
            request = scrapy.Request(url, callback=self.parse_comments, headers=h, dont_filter=True)
            request.meta['blog'] = blog
            yield request

    def parse_author(self, response, disPage):
        item = userItem()
        item['disPage'] = disPage
        user = response.xpath('//div[@class="author-details"]//a/@href').extract()[0]
        item['uid'] = user.split('/')[-1]
        item['source'] = response.urljoin(user)
        firstName = response.xpath('//span[@class="given-name"]/text()').extract()
        lastName = response.xpath('//span[@class="family-name"]/text()').extract()
        if firstName:
            item['firstName'] = firstName[0]
        if lastName:
            item['lastName'] = lastName[0]

        occupation = response.xpath('//div[@class="agent-details-col"]/div/text()').extract()
        if occupation:
            item['occupation'] = occupation[0].strip()

        rainmaker = response.xpath('//div[@class="agent-mast-img"]/div')
        if rainmaker:
            item['account'], item['points'] = self.getRainmaker(rainmaker)

        location = response.xpath('//div[@id="find_agents"]/p/a/@href').extract()
        if location:
            item['state'], item['city'] = [i.split('/')[-1] for i in location]

        return item

    def parse_user(self, c, disPage):
        item = userItem()
        item['disPage'] = disPage

        user = c.xpath('div[@class="comment-left-section"]/a/@href').extract()
        if not user:
            user = c.xpath('.//div[@class="comment-author"]/text()').extract()
        item['uid'] = user[0].split('/')[-1]
        item['source'] = 'http://activerain.com' + user[0]

        name = c.xpath('.//div[@class="comment-author"]/text()').extract()
        if name:
            item['firstName'], item['lastName'] = self.getName(name[0])

        occupation = c.xpath('.//div[@class="tagline"]/text()').extract()
        if occupation:
            item['occupation'] = occupation[0].strip()

        rainmaker = c.xpath('.//div[@class="comment-header"]/div')
        if rainmaker:
            item['account'], item['points'] = self.getRainmaker(rainmaker)

        location = c.xpath('.//div[@class="company"]/text()').extract()
        if location:
            l = location[0].split('-')[-1].strip()
            if ',' in l:
                item['city'], item['state'] = l.split(',') if l else (None, None)

        return item

    def parse_comments(self, response):
        blog = response.meta['blog']
        count = blog['count']
        d = json.loads(response.text)
        for id in d:
            for i in d[id]:
                count += 1
                c = Selector(text=i)
                item = postItem()
                uItem = userItem()
                item['URL'] = blog['URL']
                item['title'] = blog['title']
                item['disPage'] = blog['blogPage']
                item['pid'] = int(c.xpath('//div[@class="blog-comment-comment "]/@data-id').extract()[0])
                item['replyid'] = count
                t = c.xpath('.//meta[@itemprop="datePublished"]/@content').extract()[0]
                item['postTime'] = datetime.strptime(t, '%Y-%m-%dT%H:%M:%S')
                item['replyTo'] = blog['replyid'].get(id)
                # Ignore deleted post
                if not item['replyTo']:
                    continue
                body = c.xpath('.//div[@class="blog-comment-comment-body"]//text()').extract()
                item['body'] = ''.join(body).strip()
                uid = c.xpath('//div[@class="blog-comment-comment-details"]/div/@data-id').extract()[0]
                item['uid'] = uid
                uItem['uid'] = uid
                name = c.xpath('//div[contains(@class, "agent-tag")]/text()').extract()[0]
                uItem['firstName'], uItem['lastName'] = self.getName(name)
                url = 'http://activerain.com/profile/{0}/mini_vcard'.format(uid)
                request = scrapy.Request(url, callback=self.parse_mini_card, dont_filter=True)
                request.meta['item'] = item
                request.meta['uItem'] = uItem
                request.meta['handle_httpstatus_list'] = [404]
                yield request

    def parse_mini_card(self, response):
        if response.status in response.meta['handle_httpstatus_list']:
            yield response.meta['uItem']
            yield response.meta['item']
            return

        pItem = response.meta['item']
        user = response.xpath('//a[@target="_blank"]/@href').extract()[0]
        uid = user.split('/')[-1]
        pItem['uid'] = uid
        if uid in self.users:
            yield pItem
            return

        self.users.add(uid)
        item = userItem()
        item['disPage'] = pItem['disPage']
        item['uid'] = uid
        name = response.xpath('//h5[@class="userInfo__content-name"]/text()').extract()[0]
        item['firstName'], item['lastName'] = self.getName(name)
        item['source'] = response.urljoin(user)
        request = scrapy.Request(item['source'], callback=self.parse_profile, dont_filter=True)
        request.meta['item'] = item
        request.meta['pItem'] = pItem
        yield request

    def parse_profile(self, response):
        item = response.meta['item']
        occupation = response.xpath('//h2[@class="userCard__userInfo-agent-subtitle"]/span/text()').extract()
        if occupation:
            item['occupation'] = occupation[0].strip()

        location = response.xpath('//span[@class="userCard__userInfo-agent-market-location"]/text()').extract()
        location = [i.strip() for i in location if i.strip()]
        if location:
            item['city'], item['state'] = location[0].split(',')

        rainmaker = response.xpath('//div[@class="userCard__content-userType-info"]/span/text()').extract()
        if rainmaker:
            item['account'] = rainmaker[0]
            item['points'] = int(filter(unicode.isdigit, rainmaker[1]))

        yield item
        self.users.add(item['uid'])
        yield response.meta['pItem']

    def getName(self, n):
        name = n.split()
        return name if len(name) == 2 else ['', name[0]] if len(name) == 1 else [' '.join(name[:-1]), name[-1]] if name else ['', '']


    def getRainmaker(self, rainmaker):
        account = rainmaker[0].xpath('span/text()').extract()
        points = rainmaker[0].xpath('text()').extract()
        points = [int(filter(unicode.isdigit, i)) for i in points if i.strip()]
        return account + points if points else account + [None]










