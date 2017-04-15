import sys
import traceback
import argparse
import collections
import datetime
import tweepy
import re as regex
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



"""Define command-line args"""
parser = argparse.ArgumentParser(description="Twitter Profile Analyzer (https://github.com/nav97/Tweet-Analyzer)",
                                 usage="-n <screen_name> [options]")

parser.add_argument('-n', '--name', required=True, metavar="screen_name", 
                    help='The specified twitter user screen name')
parser.add_argument('-l', '--limit', metavar='N', type=int, default=1000, 
                    help='Specify the number of tweets to retreive going back from the latest tweet (default to 1000)')
parser.add_argument('--utc-offset', type=int,
                    help='Apply timezone offset (in seconds)')
parser.add_argument('--no-timezone', action='store_true',
                    help='Remove timezone auto-adjustment (default to UTC)')

args = parser.parse_args()

""" GLOBAL VARIABLES (to store data)"""
startDate = 0
endDate = 0

detectedUrls = collections.Counter()
detectedHashtags = collections.Counter()
mentionedUsers = collections.Counter()
retweetedUsers = collections.Counter()
detetctedLocations = collections.Counter()
detectedDevices = collections.Counter()

activityMatrix = np.zeros((7, 24))



""" Process and analyze a single tweet, updating our data"""
def process_tweet(tweet):
    global startDate
    global endDate

    #Date in UTC
    dateOfTweet = tweet.created_at
    
    #Adjust time based off user specified offset which overrides profile settings
    if(args.utc_offset):
        dateOfTweet = (tweet.created_at + datetime.timedelta(seconds=args.utc_offset))
    
    #Auto adjust time based off user profile location
    elif(tweet.user.utc_offset and not args.no_timezone):
        dateOfTweet = (tweet.created_at + datetime.timedelta(seconds=tweet.user.utc_offset))

    #Range of tweets analyzed in specified timezone
    endDate = endDate or dateOfTweet
    startDate = dateOfTweet

    #Update activityMatrix for heatmap
    activityMatrix[dateOfTweet.weekday()][dateOfTweet.hour] += 1

    #Update Domain Urls detected
    if(tweet.entities['urls']):
        for url in tweet.entities['urls']:
            domain = urlparse(url['expanded_url']).netloc
            domain = regex.sub('www.', '', domain)
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
    if(tweet.place):
        detetctedLocations[tweet.place.name] += 1

    #Update detected devices
    detectedDevices[tweet.source] += 1



""" Download Tweets from user account """
def get_tweets(api, user, limit):
    for tweet in tqdm(tweepy.Cursor(api.user_timeline, screen_name=user).items(limit), unit="tweets", total=limit):
        process_tweet(tweet)



""" Print stats to terminal"""
def print_stats(data, amount=10):
    total = sum(data.values())
    count = 0
    if total:
        sortedKeys = sorted(data, key=data.get, reverse=True)
        max_len_key = max([len(x) for x in sortedKeys][:amount])
        for key in sortedKeys:
            print(("- \033[1m{:<%d}\033[0m {:>6} {:<4}" % max_len_key
                    ).format(key, data[key], "(%d%%)" % ((float(data[key]) / total) * 100))
                    ).encode(sys.stdout.encoding, errors='replace')

            count += 1
            if count >= amount:
                break
    else:
        print("No data found")

    print("")



""" Create heatmap of user activity """
def graph_data(numOfTweets, utcOffset):
    Index = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    Cols = ["%.2d:00" %x for x in range(24)]
    activityDf = pd.DataFrame(activityMatrix, index=Index, columns=Cols)
    heatmapAxes = sns.heatmap(activityDf, annot=True)
    heatmapAxes.set_title('Heatmap of @%s Twitter Activity \n Generated %s for last %s tweets' %(args.name, datetime.date.today(), numOfTweets), fontsize=14)
    plt.xlabel("Time (UTC offset in seconds: %s)" %utcOffset)
    plt.yticks(rotation=0)
    plt.show()



def main():
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)

    print("[[-]] Getting @%s account information..." %args.name)

    user = api.get_user(screen_name=args.name)
    numOfTweets = min([args.limit, user.statuses_count])

    print("[[-]] Name           : %s" %user.name)
    print("[[-]] Description    : %s" %user.description).encode(sys.stdout.encoding, errors='replace')
    print("[[-]] Followers      : %s" %user.followers_count)
    print("[[-]] Following      : %s" %user.friends_count)
    print("[[-]] Language       : %s" %user.lang)
    print("[[-]] Geo Enabled    : %s" %user.geo_enabled)
    print("[[-]] Location       : %s" %user.location)
    print("[[-]] Time zone      : %s" %user.time_zone)
    print("[[-]] UTC offset     : %s" %user.utc_offset)
    

    if(args.utc_offset):
        print("[[!]] applying timezone offset of %s s" %args.utc_offset)

    print("[[-]] Total tweets   : %s" %user.statuses_count)
    print("")
    print("[[-]] Retrieving last %s tweets..." %numOfTweets)

    if(numOfTweets == 0):
        sys.exit()

    get_tweets(api, args.name, numOfTweets)
    print("[[-]] Success! Tweets retrieved from %s to %s (%s days)\n" %( startDate, endDate, (endDate - startDate).days ))

    print("[[-]] Top 10 Detected Hashtags")
    print_stats(detectedHashtags)
    
    print("[[-]] Top 10 Mentioned Websites")
    print_stats(detectedUrls)

    print("[[-]] Top 10 Mentioned Users")
    print_stats(mentionedUsers)

    print("[[-]] Top 10 Retweeted Users")
    print_stats(retweetedUsers)

    print("[[-]] Top 10 Detected Locations")
    print_stats(detetctedLocations)

    print("[[-]] Top 10 Detected Devices")
    print_stats(detectedDevices)

    utcOffset = args.utc_offset if args.utc_offset else user.utc_offset
    utcOffset = 0 if args.no_timezone else utcOffset
    graph_data(numOfTweets, utcOffset)



if __name__ == "__main__":
    try:
        main()
    except tweepy.error.TweepError as e:
        print("\nTwitter error: %s" %e)
    except Exception as e:
        print("\nError: %s" %e)
        traceback.print_exc()