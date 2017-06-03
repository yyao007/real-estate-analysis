# Natural Language Analysis for Real Estate Forums
This program is to analyze the posts crawled from BiggerPockets and activerain.
Now it can do:
* key phrase extraction (source: [real-estate-analysis/reanal/util/features.py](https://github.com/yyao007/real-estate-analysis/blob/master/reanal/util/features.py))
* sentiment analysis (source: [real-estate-analysis/reanal/util/sentiment.py](https://github.com/yyao007/real-estate-analysis/blob/master/reanal/util/sentiment.py))
* location extraction (source: [real-estate-analysis/reanal/util/location.py](https://github.com/yyao007/real-estate-analysis/blob/master/reanal/util/location.py))
* state/city normalization (source: [real-estate-analysis/reanal/util/convert.py](https://github.com/yyao007/real-estate-analysis/blob/master/reanal/util/convert.py))

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
* [other/](https://github.com/yyao007/real-estate-analysis/tree/master/reanal/other): Some test scripts


