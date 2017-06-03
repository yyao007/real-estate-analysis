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
* [other](https://github.com/yyao007/real-estate-analysis/tree/master/reanal/other): Some test scripts


