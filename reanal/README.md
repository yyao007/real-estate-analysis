# Natural Language Analysis for Real Estate Forums
This program is to analyze the posts crawled from BiggerPockets and activerain.
Now it can do:
* key phrase extraction (source: [util/features.py](https://github.com/yyao007/real-estate-analysis/blob/master/reanal/util/features.py))
* sentiment analysis (source: [util/sentiment.py](https://github.com/yyao007/real-estate-analysis/blob/master/reanal/util/sentiment.py))
* location extraction (source: [util/location.py](https://github.com/yyao007/real-estate-analysis/blob/master/reanal/util/location.py))
* state/city normalization (source: [util/convert.py](https://github.com/yyao007/real-estate-analysis/blob/master/reanal/util/convert.py))

## How to run
It is recommended to run this program in a virtual environment (see: [Install Dependencies](https://github.com/yyao007/real-estate-analysis#install-dependencies)). The command to run this program is:
```
$ python nlp.py TASK [-j JOB] [-c CLS [CLS ...]] [-n NORM] [-a] [-b]
```

There is also a help message from the program:
```
$ python nlp.py -h
usage: nlp.py [-h] [-a] [-b] [-j JOB] [-c CLS [CLS ...]] [-n NORM] task

natural language processing for real estate forums

positional arguments:
  task                  Choose from {features, sentiment, location, convert}
                          features: extract key phrases from posts
                          sentiment: classify each post sentiment
                          location: extract location from each post
                          convert: simplify user's city and state

optional arguments:
  -h, --help            show this help message and exit
  -a, --activerain      Process activerain (default: both)
  -b, --biggerpockets   Process BiggerPockets (default: both)
  -j JOB, --job JOB     Job to do. Use this flag with features (default: key)
                          key: find key phrase for each post
                          bigram: find bigrams from all of the posts
                          save: save all the posts to file
  -c CLS [CLS ...]      Classifiers used to classify sentiment. Use this flag with sentiment 
                          default: ['NaiveBayes', 'Vader', 'Stanford']
  -n NORM, --norm NORM  City or state to normalize. Use this flag with convert 
                          options: city, state
```

Example to run the program:
```
$ # extract top 50 key phrase from each (city, state, month)
$ python nlp.py features -j key
$ # classify the sentiment for posts from only BiggerPockets using Stanford and NaiveBayes classifier
$ python nlp.py sentiment -c Stanford NaiveBayes -b
$ # extract location from each post
$ python nlp.py location
$ # abbreviate all user's state to 2 characters if available
$ python nlp.py convert -n state
```

## Directory Structure
* [util/](https://github.com/yyao007/real-estate-analysis/tree/master/reanal/util): All source codes that the program needs
* [classifier/](https://github.com/yyao007/real-estate-analysis/tree/master/reanal/classifier): All trained classier to classify sentiment
* [data/](https://github.com/yyao007/real-estate-analysis/tree/master/reanal/data): Training datasets and some data needed by the program
* [other/](https://github.com/yyao007/real-estate-analysis/tree/master/reanal/other): Some test scripts

## CoreNLP Server Issue
Because the [Stanford CoreNLP](https://stanfordnlp.github.io/CoreNLP/index.html) library is written in java, this program uses a python wrapper from [stanford-corenlp](https://github.com/Lynten/stanford-corenlp) to run the [CoreNLP server](https://stanfordnlp.github.io/CoreNLP/corenlp-server.html). To start the server manually, use the following command:
```
$ # Download the newest CoreNLP
$ wget http://nlp.stanford.edu/software/stanford-corenlp-full-2016-10-31.zip
$ unzip stanford-corenlp-full-2016-10-31.zip
$ java -mx4g -cp "/home/yyao009/stanford-corenlp-full-2016-10-31/*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -annotators "sentiment" -threads 4 -port 9000 -timeout 30000 -quiet 1
```
Or, if you want to start the server in the program, change the following lines in [util/location.py](https://github.com/yyao007/real-estate-analysis/blob/master/reanal/util/location.py#L37):
```python
37        # self.st = StanfordCoreNLP('/home/yyao009/stanford-corenlp-full-2016-10-31/')
38        self.st = StanfordCoreNLPPLUS('http://localhost')
```
to
```python
37        self.st = StanfordCoreNLP('/path/to/stanford-corenlp-full-2016-10-31/')
38        # self.st = StanfordCoreNLPPLUS('http://localhost')
```

Currently, the CoreNLP Server is running in a screen session on v246 and every one can access it.

## Tables
There are four tables used to store the result.
#### 1. keyphrase
```
+------------+--------------+------+-----+---------+-------+
| Field      | Type         | Null | Key | Default | Extra |
+------------+--------------+------+-----+---------+-------+
| site       | varchar(500) | NO   | PRI | NULL    |       |
| city       | varchar(100) | NO   | PRI | NULL    |       |
| state      | varchar(50)  | NO   | PRI | NULL    |       |
| postTime   | datetime     | NO   | PRI | NULL    |       |
| key_phrase | varchar(100) | NO   | PRI | NULL    |       |
| tfidf      | float        | YES  |     | NULL    |       |
+------------+--------------+------+-----+---------+-------+
```
Store top 50 key phrases from every (city, state, month) posts. The tfidf score is to rank the importance of each key phrase.

#### 2. sentiment
```
+------------+--------------+------+-----+---------+-------+
| Field      | Type         | Null | Key | Default | Extra |
+------------+--------------+------+-----+---------+-------+
| site       | varchar(500) | NO   | PRI | NULL    |       |
| city       | varchar(100) | NO   | PRI | NULL    |       |
| state      | varchar(50)  | NO   | PRI | NULL    |       |
| postTime   | datetime     | NO   | PRI | NULL    |       |
| classifier | varchar(100) | NO   | PRI | NULL    |       |
| polarity   | float        | YES  |     | NULL    |       |
+------------+--------------+------+-----+---------+-------+
```
Store the sentiment of posts as a float number in range [-1, 1]. -1 is very negative while 1 is very positive. Most sentiments are between very negative and very positive.

#### 3. unigrams
```
+------------+--------------+------+-----+---------+-------+
| Field      | Type         | Null | Key | Default | Extra |
+------------+--------------+------+-----+---------+-------+
| site       | varchar(500) | NO   | PRI | NULL    |       |
| key_phrase | varchar(100) | NO   | PRI | NULL    |       |
| _df        | int(11)      | YES  |     | NULL    |       |
+------------+--------------+------+-----+---------+-------+
```
Store all the unigrams that have \_df >= 7 from all the posts. Total

#### 4. bigrams
```
+------------+--------------+------+-----+---------+-------+
| Field      | Type         | Null | Key | Default | Extra |
+------------+--------------+------+-----+---------+-------+
| site       | varchar(500) | NO   | PRI | NULL    |       |
| key_phrase | varchar(100) | NO   | PRI | NULL    |       |
| freq       | int(11)      | YES  |     | NULL    |       |
| pmi        | float        | YES  |     | NULL    |       |
+------------+--------------+------+-----+---------+-------+
```
Store top 5000 bigrams with most pmi score for each site.
