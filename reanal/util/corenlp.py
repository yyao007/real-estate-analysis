# _*_coding:utf-8_*_

# Modify stanfordcorenlp module to include sentiment analysis
from stanfordcorenlp import StanfordCoreNLP
import requests
import json

polarity_score = {'Positive': 1.0, 'Negative': -1.0, 'Neutral': 0.0}

class StanfordCoreNLPPLUS(StanfordCoreNLP):
    def sentiment(self, sentence):
        r_dict = self._request('sentiment', sentence.encode('utf-8'))
        sentiments=[s['sentiment'] for s in r_dict['sentences']]
        senti = 0
        total = len(r_dict['sentences'])
        for sent in sentiments:
            senti += polarity_score[sent]
        return senti / total

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

        




