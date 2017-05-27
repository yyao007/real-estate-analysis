from db import *
from features import Feature_extraction
from nltk import word_tokenize
from nltk.classify import NaiveBayesClassifier
from nltk.corpus import movie_reviews
from nltk.sentiment import SentimentAnalyzer
from nltk.sentiment.util import *
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from datetime import datetime
import pickle
import os

seperator = '-' * 12
naivebayes_file = "NBClassifier"
polarity_score = {'pos': 1.0, 'neg': -1.0, 'neutral': 0.0}

class sentiment_analysis(Feature_extraction):

    def save_sentiment(self, url, classifier, sentiment):
        key, score = sentiment
        sent = Sentiments(
            site=url,
            city=key[0],
            state=key[1], 
            postTime=key[2],
            classifier=classifier,
            polarity=score,
        )
        self.session.add(sent)
        self.session.commit()

    def iter_posts(self, url):
        # create a generator to iterate through each post
        url_like = '%' + url + '%'
        posts = self.session.query(Posts.body, Users.city, Users.state).join(Users).filter(Posts.URL.like(url_like)).filter(func.length(Users.state)==2)
        # location = self.session.query(Users.city, Users.state).filter(Users.source.like(url_like)).filter(func.length(Users.state)==2).group_by(Users.city, Users.state)
        start_date = self.session.query(Posts.postTime).filter(Posts.URL.like(url_like)).order_by(Posts.postTime).first()
        end_date = self.session.query(Posts.postTime).filter(Posts.URL.like(url_like)).order_by(Posts.postTime.desc()).first()

        # To calculate tfidf of posts from each city, each month
        docs = {}
        for monthrange in self.iter_monthrange(start_date[0], end_date[0]):
            print '{}--{} :'.format(monthrange[0], monthrange[1])
            # sys.stdout.flush()
            count = 0
            monthlyPosts = posts.filter(Posts.postTime.between(monthrange[0], monthrange[1])).order_by(Users.city, Users.state)
            # monthlyPosts = posts.filter(Users.city=='CAMBRIDGE').filter(Users.state=='MA').filter(Posts.postTime.between(monthrange[0], monthrange[1]))
            # print monthlyPosts.statement.compile(self.engine)
            text = []
            previous = ('', '')
            for post in monthlyPosts:
                city = post.city.strip().lower()
                city = ' '.join(i[0].upper()+i[1:] for i in city.split())
                state = post.state.strip().upper()
                if city == previous[0] and state == previous[1]:
                    tokens = [t.lower() for t in word_tokenize(post.body) if not self.filter_func(t)]
                    text.append(tokens)
                else: 
                    if text:
                        key = (previous[0], previous[1], monthrange[0])
                        count += 1
                        yield (key, text)
                        
                    tokens = [t.lower() for t in word_tokenize(post.body) if not self.filter_func(t)]
                    text = [tokens]
                    previous = (city, state)
                    
            # To save the last city in the result query
            if text:
                key = (post.city, post.state, monthrange[0])
                count += 1
                yield (key, text)
                
            print 'total: {}'.format(count)

    def load_data(self, classifier=None):
        # source: http://www.nltk.org/book/ch06.html, http://www.nltk.org/howto/sentiment.html
        print "Loading training data...",
        sys.stdout.flush()
        documents = [(word_tokenize(movie_reviews.raw(fileid)), category)
                    for category in movie_reviews.categories()
                    for fileid in movie_reviews.fileids(category)]
        random.shuffle(documents)
        cutoff = int(len(documents) * 0.1)
        training_docs, testing_docs = documents[cutoff:], documents[:cutoff]
        print "Done!"
        
        print "Extracting unigram features and applying to training data...",
        sys.stdout.flush()
        sentim_analyzer = SentimentAnalyzer(classifier=classifier)
        all_words = sentim_analyzer.all_words([mark_negation(doc) for doc in training_docs])
        unigram_feats = sentim_analyzer.unigram_word_feats(all_words, top_n=5000)
        unigrams = [w for w in unigram_feats if not self.filter_func(w)]
        # print len(unigrams)
        sentim_analyzer.add_feat_extractor(extract_unigram_feats, unigrams=unigrams, handle_negation=True)
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
        # sentim_analyzer, training_set, testing_set = self.load_data(classifier=classifier)
        for key,value in sorted(sentim_analyzer.evaluate(testing_set).items()):
            print('{0}: {1}'.format(key, value)) 

    def polarity(self, docs, **kwargs):
        NaiveBayes, Vader = kwargs['NaiveBayes'], kwargs['Vader']
        score = 0
        total = len(docs)
        if NaiveBayes:
            doc_set = NaiveBayes.apply_features(docs, labeled=False)
            sents = NaiveBayes.classifier.classify_many(doc_set)
            for sent in sents:
                score += polarity_score[sent]
        elif Vader:
            for doc in docs:
                text = ' '.join(doc)
                score += Vader.polarity_scores(text)['compound']
        
        return score / total        

    def classify_posts(self, url, classifier, **kwargs):
        print "Calculating sentiment for {}".format(url)

        count = 0
        for post in self.iter_posts(url):
            if count % 100 == 0:
                print 'classified {} posts'.format(count)
            count += 1
            print "sentiment for {} (total: {}):".format(post[0], len(post[1])),
            sys.stdout.flush()
            # calculate polarity score for each post
            score = self.polarity(post[1], **kwargs)
            print "{0:.2f}".format(score)
            sentiment = (post[0], score)
            self.save_sentiment(url, classifier, sentiment)             
            


if __name__ == '__main__':
    
    urls = ['BiggerPockets', 'activerain']
    # urls = ['activerain']
    classifiers = ['NaiveBayes', 'Vader']
    classifiers = ['Vader']
    NaiveBayes = Vader = None
   
    for url in urls:
        sentiment = sentiment_analysis()
        for classifier in classifiers:
            if classifier == 'NaiveBayes':
                NaiveBayes = sentiment_analysis.NaiveBayes_load()
            elif classifier == 'Vader':
                Vader = SentimentIntensityAnalyzer()
            
            start_time = datetime.now()
            print '{}Classify posts from {} using {}{}'.format(seperator, url, classifier, seperator)
            sentiment.classify_posts(url, classifier, NaiveBayes=NaiveBayes, Vader=Vader)
            end_time = datetime.now()
            print 'Total time for {} using {}: {}'.format(url, classifier, end_time - start_time)























        