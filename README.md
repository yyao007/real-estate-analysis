#Real Estate Analysis.
There are three projects in this repo:
##1. BiggerPockets
Crawler for [BiggerPockets](https://www.biggerpockets.com/forums) forums.
##2. activerain
Crawler for [activerain](http://activerain.com/bloghome) posts.
##3. anals
⋅⋅1. Analyze the posts from both sites using natural language processing tools (nltk and sklearn) to find the key phrase for every city, state in every month.
⋅⋅2. Use machine learning methods such as Naive Bayes Classifier to identify sentiment for posts from every city, state in every month.

#Directory Structure
```
real-estate-analysis
|____requirements.txt
|____README
|____reanal
| |____log
| | |____out.txt
| | |____sent.txt
| |____classifier
| | |____NBClassifier_backup
| |______init__.py
| |____data
| | |____stop-word-list.txt
| | |____activerain_posts.txt
| | |____BiggerPockets_posts.txt
| | |____abbr.txt
| | |____BiggerPockets_posts_test.txt
| |____other
| | |____tensorflow.sh
| |____util
| | |____sentiment.py
| | |____db.pyc
| | |______init__.py
| | |____features.pyc
| | |______init__.pyc
| | |____features.py
| | |____convert-state.py
| | |____db.py
| |______init__.pyc
| |____nlp.py
```

#Install Dependencies
To install dependencies, create a [virtual environment](https://virtualenv.pypa.io/en/stable/userguide/) first. In the virtual enviroment, run
```
pip install -r requirements.txt
```

