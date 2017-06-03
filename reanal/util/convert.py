# -*- coding: utf-8 -*-
from db import Users, DB
from sqlalchemy import update
from sqlalchemy.engine import ResultProxy
import sys
import os

path = os.path.dirname(__file__)
filename = os.path.join(path, '../data/abbr.txt')

class Convert:
    def __init__(self, file=filename):
        db = DB()
        self.session = db.get_session()
        self.file = file
        self.abbr = self.load_abbr(self.file)

    def load_abbr(self, file):
        with open(file, 'r') as f:
            contents = f.read()
            lines = [l.split('\t') for l in contents.split('\n')]
            d = {}
            for l in lines:
                d[l[0].lower()] = l[2]
                d[l[1].lower()] = l[2]
                d[l[2].lower()] = l[2]
            f.close()
        return d

    def abbreviate(self, state):
        s = state.lower().strip()
        a = self.abbr.get(s)
        if not a:
            s = s.split('(')[0].split(',')[0].split('-')[0].strip()
            a = self.abbr.get(s)
        if not a:
            s = s.replace('.', '')
            a = self.abbr.get(s)
        if not a:
            s = state.lower().strip().split(',')
            if len(s) > 1:
                s = s[1].strip()
                a = self.abbr.get(s)
        if not a:
            s = state.lower().strip().split('&')[0].split('and')[0].strip()
            a = self.abbr.get(s)

        return a

    def abbr_state(self):
        states = self.session.execute('select distinct(state) from forumusers')
        count = 0
        for state in states:
            if not state[0]:
                continue
            a = self.abbreviate(state[0])
            if a:
                if state[0].isupper() and len(state[0]) == 2:
                    continue
                count += 1
                print 'Abbreviating state {} to {}'.format(state[0], a)
                r = self.session.execute('update forumusers set state=\'{}\' where state=\'{}\''.format(a, state[0]))
                print "{} rows changed".format(r.rowcount)
                self.session.commit()

        return count

    def norm_city(self):
        count = 0
        for city in self.session.query(Users.city.distinct()):
            if not city[0]:
                continue
            c = city[0].strip().lower()
            c = ' '.join(i[0].upper()+i[1:] for i in c.split())
            if c != city[0]:
                count += 1
                print 'Normalizing city {} to {}'.format(city[0], c)
                stmt = update(Users).where(Users.city==city[0]).values(city=c)
                r = self.session.execute(stmt)
                print "{} rows changed".format(r.rowcount)
                self.session.commit()

        return count

    def start(self, task):
        if task == 'state':
            print "Start abbreviating states..."
            count = self.abbr_state()
            print "Done! {} states changed".format(count)
        elif task == 'city':
            print "Start normalizing cities..."
            count = self.norm_city()
            print "Done! {} cities changed".format(count)        


if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print 'Usage: python convert-state.py state/city'
        exit()
    if len(sys.argv) > 1:
        task = sys.argv[1]
        if task == 'state':
            c = Convert()
            print "Start abbreviating states..."
            count = c.abbr_state()
            print "Done! {} states changed".format(count)
        elif task == 'city':
            c = Convert()
            print "Start normalizing cities..."
            count = c.norm_city()
            print "Done! {} cities changed".format(count)






