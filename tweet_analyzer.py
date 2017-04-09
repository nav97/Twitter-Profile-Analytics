import sys
import traceback
import argparse
import collections
import datetime
import tweepy
import numpy as np
from ascii_graph import Pyasciigraph
from ascii_graph.colors import Gre, Yel, Red
from ascii_graph.colordata import hcolor
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
detetctedLocations = collections.Counter()
detectedLanguages = collections.Counter()




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

    #Update weekly activity -> Goes to graph

    #Update Domain Urls detected

    #Update Retweets

    #Update Hashtag List

    #Update Mentioned Users

    #Update detetcted locations

    #Update detected languages



""" Download Tweets from user account """
def get_tweets(api, user, limit):
    for tweet in tqdm(tweepy.Cursor(api.user_timeline, screen_name = user).items(limit), bar_format='l_bar'):
        process_tweet(tweet)

def print_stats():
    return

def print_charts():
    return


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
        print("Twitter error: %s" %e)
    except Exception as e:
        print("Error: %s" %e)
        traceback.print_exc()

