from sqlalchemy import create_engine, distinct
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Integer, String, DateTime, Text, TIMESTAMP, Float
from sqlalchemy.sql import func
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.ext.declarative import declarative_base

connStr = 'mysql+mysqldb://yuan:931005@127.0.0.1/homeDB'
Base = declarative_base()
class Posts(Base):
    __tablename__ = 'forumposts'
    URL = Column(String(500), primary_key=True)
    replyid = Column(Integer, primary_key=True)
    pid = Column(Integer) # post id
    title = Column(String(500))
    category = Column(String(500)) # discussion category
    categoryURL = Column(String(500))
    uid = Column(String(50), ForeignKey('forumusers.uid', onupdate="CASCADE", ondelete='CASCADE')) # user id
    replyTo = Column(Integer) # This is the first post id of the discussion
    postTime = Column(DateTime(timezone=True)) # precise to hour eg. 2017-02-11 19:00:00
    body = Column(Text)
    likes = Column(Integer)
    tags = Column(String(500))
    city = Column(String(100))
    state = Column(String(50))

class Users(Base):
    __tablename__ = 'forumusers'

    uid = Column(String(50), primary_key=True) # user id
    firstName = Column(String(200))
    lastName = Column(String(100))
    source = Column(String(100)) # URL of the user profile
    colleagues = Column(Integer)
    followers = Column(Integer)
    following = Column(Integer)
    numPosts = Column(Integer)
    numVotes = Column(Integer)
    numAwards = Column(Integer)
    points = Column(Integer)
    account = Column(String(50)) # account type: base, plus, pro
    city = Column(String(100))
    state = Column(String(50))
    dateJoined = Column(DateTime) # creation date of the user account
    seeking = Column(Text) # currently seeking
    experience = Column(Text) # real estate experience
    occupation = Column(String(767))
    goals = Column(Text) # real estate goals
    crawl_time = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class Cities(Base):
    __tablename__ = 'cities'

    city = Column(String(50), primary_key=True)
    state = Column(String(2), primary_key=True)

class Keyphrase(Base):
    __tablename__ = 'keyphrase'

    site = Column(String(500), primary_key=True)
    city = Column(String(100), primary_key=True)
    state = Column(String(50), primary_key=True)
    postTime = Column(DateTime(timezone=True), primary_key=True)
    key_phrase = Column(String(100), primary_key=True)
    tfidf = Column(Float(precision=6))

class Bigrams(Base):
    __tablename__ = 'bigrams'

    site = Column(String(500), primary_key=True)
    key_phrase = Column(String(100), primary_key=True)
    freq = Column(Integer)
    pmi = Column(Float(precision=5))

class Unigrams(Base):
    __tablename__ = 'unigrams'

    site = Column(String(500), primary_key=True)
    key_phrase = Column(String(100), primary_key=True)
    _df = Column(Integer)

class Sentiments(Base):
    __tablename__ = 'sentiments'
    site = Column(String(500), primary_key=True)
    city = Column(String(100), primary_key=True)
    state = Column(String(50), primary_key=True)
    postTime = Column(DateTime(timezone=True), primary_key=True)
    classifier = Column(String(100), primary_key=True)
    polarity = Column(Float(precision=5))

class DB:
    def __init__(self):
        self.engine = create_engine(connStr, pool_size=20, convert_unicode=True, echo=False)
        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)
        Base.metadata.create_all(self.engine)

    def get_session(self):
        return self.Session

    def new_session(self):
        self.New_Session = scoped_session(self.session_factory)
        return self.New_Session

    def remove(self):
        self.Session.remove()
        


