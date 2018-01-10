# -*- coding: utf-8 -*-
import sys
import argparse
from functools import wraps
from datetime import datetime

def timeit(f):
    def wrap(*args, **kw):
        ts = datetime.now()
        result = f(*args, **kw)
        te = datetime.now()
        site = kw.get('site')
        print 'total time for {} on {}: {}'.format(\
                f.__name__, site, te-ts)
        return result
    return wrap

@timeit
def process_features(job, site):
    feature = Feature_extraction()
    feature.start(job, site)

@timeit
def process_sentiment(classifier, site):
    core = 8
    sentiment = sentiment_analysis(core)
    sentiment.start(classifier, site)

@timeit
def process_location():
    loc = Location()
    loc.process_posts()

@timeit
def process_convert(norm):
    c = Convert()
    c.start(norm)

def get_parser():
    tasks = ['features', 'sentiment', 'location', 'convert']
    jobs = ['key', 'bigram', 'save']
    classifiers = ['NaiveBayes', 'Vader']
    norms = ['city', 'state']

    parser = argparse.ArgumentParser(
        description='natural language processing for real estate forums',
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument('task', choices=tasks, metavar='task',
                help='''Choose from {%(choices)s}
  features: extract key phrases from posts
  sentiment: classify each post sentiment
  location: extract location from each post
  convert: simplify user's city and state''')
    parser.add_argument('-a', '--activerain', action='store_true',
                help='Process activerain (default: both)')
    parser.add_argument('-b', '--biggerpockets', action='store_true',
                help='Process BiggerPockets (default: both)')
    parser.add_argument('-j', '--job', choices=jobs, default='key',
                metavar='JOB', help='''Job to do. Use this flag with features (default: %(default)s)
  key: find key phrase for each post
  bigram: find bigrams from all of the posts
  save: save all the posts to file''')
    parser.add_argument('-c', choices=classifiers, default=classifiers,
                dest='classifiers', metavar='CLS', nargs='+',
                help='''Classifiers used to classify sentiment. Use this flag with sentiment
  default: %(default)s''')
    parser.add_argument('-n', '--norm', choices=norms, metavar='NORM',
                help='''City or state to normalize. Use this flag with convert
  options: %(choices)s''')
    return parser


if __name__ == '__main__':
    parser = get_parser()
    args = parser.parse_args()
    # handle sites
    sites = []
    if args.activerain:
        sites.append('activerain')
    if args.biggerpockets:
        sites.append('BiggerPockets')
    if not sites:
        sites = ['BiggerPockets', 'activerain']

    if args.task == 'features':
        from util.features import Feature_extraction
        for site in sites:
            process_features(args.job, site)

    elif args.task == 'sentiment':
        from util.sentiment import sentiment_analysis
        for site in sites:
            print args.classifiers, site
            process_sentiment(args.classifiers, site)

    elif args.task == 'location':
        from util.location import Location
        process_location()

    elif args.task == 'convert':
        from util.convert import Convert
        if not args.norm:
            print 'Error: Must specify a normalization'
            exit(0)
        process_convert(args.norm)
