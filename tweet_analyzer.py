import sys
import traceback
import argparse
import collections
import datetime
import tweepy
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from tqdm import tqdm

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

from auth import CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET


"""User-friendly command-line interface"""
parser = argparse.ArgumentParser(description="Twitter Profile Analyzer (https://github.com/nav97/Tweet-Analyzer)",
                                 usage="-n <screen_name> [options]")

parser.add_argument('-n', '--name', required=True, metavar="screen_name", 
                    help='target screen_name')
parser.add_argument('-l', '--limit', metavar='N', type=int, default=1000, 
                    help='limit the number of tweets to retreive (default=1000)')
parser.add_argument('--utc-offset', type=int,
                    help='manually apply a timezone offset (in seconds)')

args = parser.parse_args()

""" GLOBAL VARIABLES (to store data)"""
startDate = 0
endDate = 0


detectedUrls = collections.Counter()
detectedRetweets = collections.Counter()
detectedHashtags = collections.Counter()
mentionedUsers = collections.Counter()
retweetedUsers = collections.Counter()
detetctedLocations = collections.Counter()
detectedLanguages = collections.Counter()


hourlyActivity = {"%.2d:00" %hour: 0 for hour in range (24)}
weeklyActivity = {"%s" %day: 0 for day in range(7)}
activityMatrix = np.zeros((7, 24))


""" Process and analyze a single tweet, updating our data"""
def process_tweet(tweet):
    global startDate    #BAD needs to be changed asap
    global endDate

    #Get date range of tweets (start at most recent tweet)
    dateOfTweet = tweet.created_at
    endDate = endDate or dateOfTweet
    startDate = dateOfTweet
    
    #Update time based off timezone and specified offset

    #Update hourly activity -> Goes to graph
    hourlyActivity["%.2d:00" %dateOfTweet.hour] += 1

    #Update weekly activity -> Goes to graph
    weeklyActivity[str(dateOfTweet.weekday())] += 1

    #Update activityMatrix for heatmap
    activityMatrix[dateOfTweet.weekday()][dateOfTweet.hour] += 1

    #Update Domain Urls detected
    if(tweet.entities['urls']):
        for url in tweet.entities['urls']:
            domain = urlparse(url['expanded_url']).netloc
            detectedUrls[domain] += 1 if (domain != "twitter.com") else (0)

    #Update Retweets
    if hasattr(tweet, 'retweeted_status'):
        retweetedUsers[tweet.retweeted_status.user.screen_name] += 1

    #Update Hashtag List
    if(tweet.entities['hashtags']):
        for hashtag in tweet.entities['hashtags']:
            detectedHashtags[hashtag['text']] += 1

    #Update Mentioned Users
    if(tweet.entities['user_mentions']):
        for user in tweet.entities['user_mentions']:
            mentionedUsers[user['screen_name']] += 1

    #Update detetcted locations

    #Update detected languages

    #Update detected devices



""" Download Tweets from user account """
def get_tweets(api, user, limit):
    for tweet in tqdm(tweepy.Cursor(api.user_timeline, screen_name=user).items(limit), unit="tweet", total=limit):
        process_tweet(tweet)
    
    create_graphs()

def print_report():
    return

def create_graphs():

    Index = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    Cols = ["%.2d:00" %x for x in range(24)]
    activity = pd.DataFrame(activityMatrix, index=Index, columns=Cols)

    heatmap = sns.heatmap(activity, annot=True, linewidths=0.5)
    plt.show()


def main():
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)

    print("[[-]] Getting @%s account information..." %args.name)

    user = api.get_user(screen_name=args.name)
    numOfTweets = np.amin([args.limit, user.statuses_count])

    print("[[-]] name           : %s" %user.name)
    print("[[-]] description    : %s" %user.description)
    print("[[-]] followers      : %s" %user.followers_count)
    print("[[-]] following      : %s" %user.friends_count)
    print("[[-]] language       : %s" %user.lang)
    print("[[-]] geo enabled    : %s" %user.geo_enabled)
    print("[[-]] location       : %s" %user.location)
    print("[[-]] time zone      : %s" %user.time_zone)
    print("[[-]] utc offset     : %s" %user.utc_offset)
    

    if(args.utc_offset):
        print("[[!]] applying timezone offset of %s s" %args.utc_offset)

    print("[[-]] tweets         : %s" %user.statuses_count)
    print("")
    print("[[-]] Retrieving last %s tweets..." %numOfTweets)
    get_tweets(api, args.name, numOfTweets)
    print("[[-]] Success! Tweets retrieved from %s to %s (%s days)" %( startDate, endDate, (endDate - startDate).days ))

if __name__ == "__main__":
    try:
        main()
    except tweepy.error.TweepError as e:
        print("\nTwitter error: %s" %e)
    except Exception as e:
        print("\nError: %s" %e)
        traceback.print_exc()

