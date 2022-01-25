import datetime
import streamlit as st
import pandas as pd
import tweepy
import re
from textblob import TextBlob
from login import *
import logging
import typing

logger = logging.getLogger()


class Tweets:
    def __init__(self, usernames: typing.List[str]):
        self.usernames = usernames
        self.accounts = dict()
        self.full_data = []

        self.tweets_data = dict()

        for username in self.usernames:
            self.getUsers(username)

        for user, id in self.accounts.items():
            self.getTweets(id, user)
            row = {'username': self.tweets_data['username'],
                    'tweet': self.tweets_data['tweet'],
                    'tweeted': self.tweets_data['tweeted'],
                    'objectivity': self.tweets_data['objectivity'],
                    'sentiment': self.tweets_data['sentiment']}
            self.full_data.append(row)


        self.showData(self.full_data)


    def getClient(self):
        client = tweepy.Client(bearer_token=BEARER_TOKEN,
                               consumer_key=API_KEY,
                               consumer_secret=API_SECRET,
                               access_token=ACCESS_TOKEN,
                               access_token_secret=ACCESS_SECRET)
        return client

    def getUsers(self, username):
        client = self.getClient()
        users = client.get_user(username=username, expansions='pinned_tweet_id', user_fields='created_at')
        self.accounts[username] = users.data.id
        logger.warning('Requesting users | getting %s', username)


    def getTweets(self, id, user):
        client = self.getClient()
        data = client.get_users_tweets(id=id, max_results=5, tweet_fields=['created_at'], exclude='retweets')
        tweet = data.data[0]
        self.tweets_data['username'] = user
        twt = self.cleanTwt(tweet.text)
        self.tweets_data['tweet'] = twt
        date = datetime.datetime.strftime(tweet.created_at,'%Y-%m-%d %H:%M')
        self.tweets_data['tweeted'] = date
        self.analyse(self.tweets_data['tweet'])



    def cleanTwt(self, twt):
        twt = re.sub('\\n', '', twt)
        twt = re.sub('#[A-Za-z0-9]+', '', twt)
        # twt = re.sub(r"http\S+", '', twt)
        return twt

    def getSubj(self, twt):
        return TextBlob(twt).sentiment.subjectivity

    def getPol(self, twt):
        return TextBlob(twt).sentiment.polarity

    def getSent(self, score):
        if score < 0:
            return 'Negative'
        elif score == 0:
            return 'Neutral'
        else:
            return 'Positive'

    def getSent2(self, score):
        if score == 0:
            return 'Objective'
        elif score > 0 and score < 1.0:
            return 'Subjective'
        else:
            return 'Very Subjective'

    def analyse(self, tweet):
        p = round(self.getPol(tweet), 3)
        s = round(self.getSubj(tweet), 3)
        self.tweets_data['polarity'] = str(p)
        self.tweets_data['subjectivity'] = str(s)
        self.tweets_data['objectivity'] = self.getSent(float(self.tweets_data['polarity']))
        self.tweets_data['sentiment'] = self.getSent2(float(self.tweets_data['subjectivity']))


    def showData(self, data):
        df = pd.DataFrame(data)
        df.set_index('username', inplace=True)
        st.dataframe(df, height=1200)
