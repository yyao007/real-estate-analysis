# -*- coding: utf-8 -*-

'''
    sentiment dataset: https://archive.ics.uci.edu/ml/datasets/Sentiment+Labelled+Sentences

'''

from db import *
from features import filter_func, iter_monthrange
from corenlp import StanfordCoreNLPPLUS
from nltk import word_tokenize
from nltk.classify import NaiveBayesClassifier
from nltk.corpus import movie_reviews
from nltk.sentiment import SentimentAnalyzer
from nltk.sentiment.util import *
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from datetime import datetime
from multiprocessing.dummy import Pool as ThreadPool
from functools import partial
import pickle
import os

seperator = '-' * 12
directory = os.path.dirname(__file__)
relpath = '../classifier/NBClassifier'
naivebayes_file = os.path.join(directory, relpath)
polarity_score = {
    'pos': 1.0,
    'positive': 1.0,
    '1': 1.0,
    'neg': -1.0,
    'negative': -1.0,
    '0': -1.0,
    'neutral': 0.0,
}

def get_stopwords():
    relpath = '../data/stop-word-list.txt'
    filename = os.path.join(directory, relpath)
    with open(filename, 'r') as f:
        stopwords1 = [l.strip().lower() for l in f]
    f.close()
    custom_stopwords = ['com', 'www', 'www2', 'org', 'http', 'https', 'bigger', 'pockets', 'active', 'rain', 'url']
    stopwords2 = nltk.corpus.stopwords.words('english')
    return set(stopwords1 + stopwords2 + custom_stopwords)


class sentiment_analysis(object):
    def __init__(self, threads=24):
        database = DB()
        self.session = database.get_session()
        self.new_session = database.new_session()
        self.pool = ThreadPool(threads)
        self.stopwords = get_stopwords()

    def save_sentiment(self, url, sentiment):
        key, score = sentiment
        sent = Sentiments(
            site=url,
            city=key[0],
            state=key[1],
            postTime=key[2],
            NaiveBayes=score['NaiveBayes'],
            Vader=score['Vader']
        )
        self.session.add(sent)
        self.session.commit()
        self.session.remove()

    def update_post_sentiment(self, post, score):
        r = self.session.query(Posts).filter(Posts.URL==post.URL).\
            filter(Posts.replyid==post.replyid).update(score)
        self.session.commit()

    def isClassified(self, key, classifier):
        classified = self.new_session.query(Sentiments).\
            filter(Sentiments.classifier==classifier).\
            filter(Sentiments.city==key[0]).filter(Sentiments.state==key[1]).\
            filter(Sentiments.postTime==key[2]).first()
        # self.new_session.remove()
        return True if classified else False

    def iter_posts(self, url, start_date=None, end_date=None):
        # create a generator to iterate through each post
        url_like = '%' + url + '%'
        posts = self.session.query(Posts.URL, Posts.replyid, Posts.body, Posts.city, Posts.state).\
                filter(Posts.URL.like(url_like)).filter(func.length(Posts.state)==2)
        # location = self.session.query(Users.city, Users.state).filter(Users.source.like(url_like)).filter(func.length(Users.state)==2).group_by(Users.city, Users.state)
        if not start_date:
            start_date = self.session.query(Posts.postTime).filter(Posts.URL.like(url_like)).order_by(Posts.postTime).first()
        if not end_date:
            end_date = self.session.query(Posts.postTime).filter(Posts.URL.like(url_like)).order_by(Posts.postTime.desc()).first()

        for monthrange in iter_monthrange(start_date[0], end_date[0]):
            print '{}--{} :'.format(monthrange[0], monthrange[1]),
            # sys.stdout.flush()
            count = 0
            monthlyPosts = posts.filter(Posts.postTime.between(monthrange[0], monthrange[1])).\
                    order_by(Posts.city, Posts.state)
            # monthlyPosts = posts.filter(Posts.city=='Orange Park').filter(Posts.state=='FL').filter(Posts.postTime.between(monthrange[0], monthrange[1]))
            # print monthlyPosts.statement.compile(self.engine)
            text = []
            previous = ('', '')
            for post in monthlyPosts:
                city = post.city.strip().lower()
                city = ' '.join(i[0].upper()+i[1:] for i in city.split())
                state = post.state.strip().upper()
                if city == previous[0] and state == previous[1]:
                    # tokens = [t.lower() for t in word_tokenize(post.body) if not filter_func(t)]
                    text.append(post)
                else:
                    if text:
                        key = (previous[0], previous[1], monthrange[0])
                        # check if this city is already been classified
                        # if not self.isClassified(key, classifier):
                        count += 1
                        yield (key, text)

                    # tokens = [t.lower() for t in word_tokenize(post.body) if not filter_func(t)]
                    data = {'url': post.URL, 'replyid': post.replyid, 'body': post.body}
                    text = [post]
                    previous = (city, state)

            # To yield the last city in the result query
            if text:
                key = (post.city, post.state, monthrange[0])
                # if not self.isClassified(key, classifier):
                count += 1
                yield (key, text)

            print 'total: {}'.format(count)

    def load_tweets(self):
        stopwords = get_stopwords()
        filename = os.path.join(directory, '../data/utf_8full_training_dataset.csv')
        tweets = {}
        with open(filename, 'r') as f:
            data = csv.reader(f)
            for d in data:
                key = re.sub(r'\W', '', d[0])
                tokens = [t.lower().encode('utf-8') for t in word_tokenize(d[1].decode('utf-8')) if not filter_func(t, stopwords)]
                if tweets.get(key):
                    tweets[key].append(tokens)
                else:
                    tweets[key] = [tokens]
        f.close()
        # testing data cutoff
        cutoff = 0.05
        testing_docs = [(t, k) for k in tweets for t in tweets[k][:int(len(tweets[k])*cutoff)]]
        training_docs = [(t, k) for k in tweets for t in tweets[k][int(len(tweets[k])*cutoff):]]
        return training_docs, testing_docs

    def load_web_reviews(self):
        stopwords = get_stopwords()
        filenames = [
            '../data/amazon_cells_labelled.txt',
            '../data/imdb_labelled.txt',
            '../data/yelp_labelled.txt',
        ]
        reviews = {}
        for file in filenames:
            filename = os.path.join(directory, file)
            with open(filename, 'r') as f:
                for line in f:
                    d = line.strip().split('\t')
                    tokens = [t.lower().encode('utf-8') for t in word_tokenize(d[0].decode('utf-8')) if not filter_func(t, stopwords)]
                    if reviews.get(d[1]):
                        reviews[d[1]].append(tokens)
                    else:
                        reviews[d[1]] = [tokens]
            f.close()

        cutoff = 0.1
        testing_docs = [(t, k) for k in reviews for t in reviews[k][:int(len(reviews[k])*cutoff)]]
        training_docs = [(t, k) for k in reviews for t in reviews[k][int(len(reviews[k])*cutoff):]]
        return training_docs, testing_docs

    def load_data(self, classifier=None):
        # source: http://www.nltk.org/book/ch06.html, http://www.nltk.org/howto/sentiment.html
        print "Loading training data...",
        sys.stdout.flush()
        training_docs, testing_docs = self.load_web_reviews()

        # documents = [(word_tokenize(movie_reviews.raw(fileid)), category)
        #             for category in movie_reviews.categories()
        #             for fileid in movie_reviews.fileids(category)]
        # random.shuffle(documents)
        # cutoff = int(len(documents) * 0.1)
        # training_docs, testing_docs = documents[cutoff:], documents[:cutoff]
        print "Done!"

        print "Extracting unigram features and applying to training data...",
        sys.stdout.flush()
        sentim_analyzer = SentimentAnalyzer(classifier=classifier)
        all_words = sentim_analyzer.all_words([mark_negation(doc) for doc in training_docs])
        unigram_feats = sentim_analyzer.unigram_word_feats(all_words)#, top_n=5000)
        # print len(unigrams)
        sentim_analyzer.add_feat_extractor(extract_unigram_feats, unigrams=unigram_feats, handle_negation=True)
        training_set = sentim_analyzer.apply_features(training_docs)
        testing_set = sentim_analyzer.apply_features(testing_docs)
        print "Done!"
        return sentim_analyzer, training_set, testing_set

    def NaiveBayes_train(self):
        print "{}Trainging NaiveBayes Classifier{}".format(seperator, seperator)
        sentim_analyzer, training_set, testing_set = self.load_data()
        print "Training classifier and save to {}...".format(naivebayes_file),
        sys.stdout.flush()
        trainer = NaiveBayesClassifier.train
        classifier = sentim_analyzer.train(trainer, training_set)
        save_file(sentim_analyzer, naivebayes_file)
        print "Done!"
        return sentim_analyzer

    def NaiveBayes_load(self):
        if os.path.isfile(naivebayes_file):
            print "Loading NaiveBayes Classifier"
            with open(naivebayes_file, 'rb') as f:
                analyzer = pickle.load(f)
            f.close()
        else:
            analyzer = self.NaiveBayes_train()

        return analyzer

    def NaiveBayes_evaluate(self):
        sentim_analyzer = self.NaiveBayes_load()
        temp, training_set, testing_set = self.load_data()
        for key,value in sorted(sentim_analyzer.evaluate(testing_set).items()):
            print('{0}: {1}'.format(key, value))

    def polarity(self, posts, NaiveBayes=None, Vader=None, st=None):
        # classifier = 'NaiveBayes' if NaiveBayes else 'Vader' if Vader else 'Stanford' if st else ''
        score = {'NaiveBayes': 0, 'Vader': 0}
        total = 0
        for post in posts:
            postScore = 0
            tokens = [t.lower() for t in word_tokenize(post.body) if not filter_func(t, self.stopwords)]
            sent = NaiveBayes.classify(tokens)
            score['NaiveBayes'] += polarity_score[sent]
            score['Vader'] += Vader.polarity_scores(post.body)['compound']
            # s = st.sentiment(post.body)
            # if s:
            #     score['Stanford'] += s

            total += 1
            self.update_post_sentiment(post, score)

        if total == 0:
            return
        return dict(map(lambda k: (k, score[k]/total), score))

    def process_sentiment(self, post, url=None, NaiveBayes=None, Vader=None, st=None):
        # sys.stdout.flush()
        # classifier = 'NaiveBayes' if NaiveBayes else 'Vader' if Vader else 'Stanford' if st else ''
        # check if this city is already been classified
        # if self.isClassified(post[0], classifier):
        #    return

        print "sentiment for {} (total: {}):".format(post[0], len(post[1]))
        # calculate polarity score for each post
        score = self.polarity(post[1], NaiveBayes, Vader, st)
        if score:
            print "{0:.2f}".format(score)

        sentiment = (post[0], score)
        self.save_sentiment(url, sentiment)

    def classify_posts(self, url, NaiveBayes=None, Vader=None, st=None):
        # classifier = 'NaiveBayes' if NaiveBayes else 'Vader' if Vader else 'Stanford' if st else ''
        this_month = None
        last_month = self.session.query(Sentiments.postTime).filter(Sentiments.site==url).\
            order_by(Sentiments.postTime.desc()).first()
        if last_month:
            month = last_month[0].month + 1
            this_month = last_month[0].replace(month=month),
        print "Calculating sentiment for {} from {}".format(url, this_month)
        self.pool.map(partial(self.process_sentiment, url=url, NaiveBayes=NaiveBayes,\
            Vader=Vader, st=st), self.iter_posts(url, start_date=this_month))

    def start(self, classifier, site):
        NaiveBayes = Vader = st = None
        if 'NaiveBayes' in classifier:
            NaiveBayes = self.NaiveBayes_load()
        if 'Vader' in classifier:
            Vader = SentimentIntensityAnalyzer()
        if 'Stanford' in classifier:
            st = StanfordCoreNLPPLUS('http://localhost')
        print '{}Classify posts from {} using {}{}'.format(seperator, site, classifier, seperator)
        self.classify_posts(site, NaiveBayes=NaiveBayes, Vader=Vader, st=st)

if __name__ == '__main__':

    urls = ['BiggerPockets', 'activerain']
    # urls = ['activerain']
    classifiers = ['NaiveBayes', 'Vader', 'Stanford']
    classifiers = []
    NaiveBayes = Vader = st = None

    for classifier in classifiers:
        sentiment = sentiment_analysis()
        if classifier == 'NaiveBayes':
            NaiveBayes = sentiment.NaiveBayes_load()
        elif classifier == 'Vader':
            Vader = SentimentIntensityAnalyzer()
        elif classifier == 'Stanford':
            st = StanfordCoreNLPPLUS('http://localhost')
        for url in urls:
            start_time = datetime.now()
            print '{}Classify posts from {} using {}{}'.format(seperator, url, classifier, seperator)
            sentiment.classify_posts(url, NaiveBayes=NaiveBayes, Vader=Vader, st=st)
            end_time = datetime.now()
            print 'Total time for {} using {}: {}'.format(url, classifier, end_time - start_time)
