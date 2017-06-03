# -*- coding: utf-8 -*-

# Modify stanfordcorenlp module to include sentiment analysis
from stanfordcorenlp import StanfordCoreNLP
import requests
import json

polarity_score = {'Verypositive': 100, 'Positive': 75, 'Neutral': 50, 'Negative': 25, 'Verynegative': 0}

# normalize score to range [-1, 1]
def nomarlize(num):
    return num / 50.0 - 1

class StanfordCoreNLPPLUS(StanfordCoreNLP):
    def sentiment(self, sentence):
        r_dict = {'sentences': []}
        count = 0
        while not r_dict['sentences']:
            # retry 1 time
            if count >= 2:
                return
            r_dict = self._request('sentiment', sentence.encode('utf-8'))
            count += 1
    
        sentiments=[s['sentiment'] for s in r_dict['sentences']]
        senti = 0
        total = len(r_dict['sentences'])
        for sent in sentiments:
            senti += polarity_score[sent]
        return nomarlize(float(senti) / total)

    # source: https://github.com/Lynten/stanford-corenlp/blob/master/stanfordcorenlp/corenlp.py
    def _request(self, annotators=None, data=None):
        properties = {'annotators': annotators, 'pipelineLanguage': self.lang, 'outputFormat': 'json'}
        r = requests.post(self.url, params={'properties': str(properties)}, data=data,
                          headers={'Connection': 'close'})
        r_dict = {'sentences': []}
        try:
            r_dict = json.loads(r.text, strict=False)
        except:
            # Retry 1 time
            r = requests.post(self.url, params={'properties': str(properties)}, data=data,
                          headers={'Connection': 'close'})
            r_dict = json.loads(r.text, strict=False)
        finally:
            return r_dict

        




