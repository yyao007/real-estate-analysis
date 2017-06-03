# Real Estate Analysis.
There are three projects in this repo:
## 1. BiggerPockets
Crawler for [BiggerPockets](https://www.biggerpockets.com/forums) forums.
## 2. activerain
Crawler for [activerain](http://activerain.com/bloghome) posts.
## 3. reanal
+ Analyze the posts from both sites using natural language processing tools (nltk and sklearn) to find the key phrase for every city, state in every month.
+ Use machine learning methods such as Naive Bayes Classifier to identify sentiment for posts from every city, state in every month.

# Directory Structure
```
.
├── BiggerPockets
│   ├── BiggerPockets
│   │   ├── __init__.py
│   │   ├── items.py
│   │   ├── middlewares.py
│   │   ├── pipelines.py
│   │   ├── settings.py
│   │   └── spiders
│   │       ├── __init__.py
│   │       └── forum.py
│   ├── LICENSE.md
│   ├── README.md
│   ├── requirements.txt
│   ├── scrapy.cfg
│   └── start.sh
├── LICENSE.md
├── README.md
├── activerain
│   ├── LICENSE.md
│   ├── README.md
│   ├── activerain
│   │   ├── __init__.py
│   │   ├── items.py
│   │   ├── middlewares.py
│   │   ├── pipelines.py
│   │   ├── settings.py
│   │   └── spiders
│   │       ├── __init__.py
│   │       └── blog.py
│   ├── scrapy.cfg
│   └── start.sh
├── reanal
│   ├── __init__.py
│   ├── classifier
│   │   ├── NBClassifier
│   │   ├── NBClassifier_movie_review
│   │   └── NBClassifier_twitter
│   ├── nlp.py
│   ├── other
│   │   └── tensorflow.sh
│   └── util
│       ├── __init__.py
│       ├── convert.py
│       ├── corenlp.py
│       ├── db.py
│       ├── features.py
│       ├── location.py
│       ├── main.py
│       └── sentiment.py
└── requirements.txt

10 directories, 40 files
```

# Install Dependencies
To install dependencies, create a [virtual environment](https://virtualenv.pypa.io/en/stable/userguide/) first. In the virtual enviroment, run
```
pip install -r requirements.txt
```

