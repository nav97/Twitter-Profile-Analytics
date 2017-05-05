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
                    help='Specify the number of tweets to retrieve going back from the latest tweet (default to 1000)')
parser.add_argument('--utc-offset', type=int,
                    help='Apply timezone offset (in seconds)')
parser.add_argument('--no-timezone', action='store_true',
                    help='Remove timezone auto-adjustment (default to UTC)')

args = parser.parse_args()

"""GLOBAL VARIABLES (to store data)"""
start_date = 0
end_date = 0

detected_urls = collections.Counter()
detected_hashtags = collections.Counter()
mentioned_users = collections.Counter()
retweeted_users = collections.Counter()
detected_locations = collections.Counter()
detected_devices = collections.Counter()

activity_matrix = np.zeros((7, 24))



"""Process and analyze a single tweet, updating our data"""
def process_tweet(tweet):
    global start_date
    global end_date

    #Date in UTC
    date_of_tweet = tweet.created_at
    
    #Adjust time based off user specified offset which overrides profile settings
    if(args.utc_offset):
        date_of_tweet = (tweet.created_at + datetime.timedelta(seconds=args.utc_offset))
    
    #Auto adjust time based off user profile location
    elif(tweet.user.utc_offset and not args.no_timezone):
        date_of_tweet = (tweet.created_at + datetime.timedelta(seconds=tweet.user.utc_offset))

    #Range of tweets analyzed in specified timezone
    end_date = end_date or date_of_tweet
    start_date = date_of_tweet

    #Update activity_matrix for heatmap
    activity_matrix[date_of_tweet.weekday()][date_of_tweet.hour] += 1

    #Update Domain Urls detected
    if(tweet.entities['urls']):
        for url in tweet.entities['urls']:
            domain = urlparse(url['expanded_url']).netloc
            domain = regex.sub('www.', '', domain)
            detected_urls[domain] += 1 if (domain != "twitter.com") else (0)

    #Update Retweets
    if hasattr(tweet, 'retweeted_status'):
        retweeted_users[tweet.retweeted_status.user.screen_name] += 1

    #Update Hashtag List
    if(tweet.entities['hashtags']):
        for hashtag in tweet.entities['hashtags']:
            detected_hashtags[hashtag['text']] += 1

    #Update Mentioned Users
    if(tweet.entities['user_mentions']):
        for user in tweet.entities['user_mentions']:
            mentioned_users[user['screen_name']] += 1

    #Update detected locations
    if(tweet.place):
        detected_locations[tweet.place.name] += 1

    #Update detected devices
    detected_devices[tweet.source] += 1



"""Download Tweets from user account"""
def get_tweets(api, user, limit):
    for tweet in tqdm(tweepy.Cursor(api.user_timeline, screen_name=user).items(limit), unit="tweets", total=limit):
        process_tweet(tweet)



"""Print stats to terminal"""
def print_stats(data, amount=10):
    total = sum(data.values())
    count = 0
    if total:
        sortedKeys = sorted(data, key=data.get, reverse=True)
        maxKeyLength = max([len(x) for x in sortedKeys])
        for key in sortedKeys:
            print(("- \033[1m{:<%d}\033[0m {:>6} {:<4}" % maxKeyLength
                    ).format(key, data[key], "(%d%%)" % ((float(data[key]) / total) * 100))
                    ).encode(sys.stdout.encoding, errors='replace')

            count += 1
            if count >= amount:
                break
    else:
        print("No data found")

    print("")



"""Create heatmap of user activity"""
def graph_data(num_of_tweets, utc_offset):
    index = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    cols = ["%.2d:00" %x for x in range(24)]
    df_activity = pd.DataFrame(activity_matrix, index=index, columns=cols)
    axes = sns.heatmap(df_activity, annot=True)
    axes.set_title('Heatmap of @%s Twitter Activity \n Generated %s for last %s tweets' %(args.name, datetime.date.today(), num_of_tweets), fontsize=14)
    plt.xlabel("Time (UTC offset in seconds: %s)" %utc_offset)
    plt.yticks(rotation=0)
    plt.show()



def main():
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)

    print("[[-]] Getting @%s account information..." %args.name)

    user = api.get_user(screen_name=args.name)
    num_of_tweets = min([args.limit, user.statuses_count])

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
    print("[[-]] Retrieving last %s tweets..." %num_of_tweets)

    if(num_of_tweets == 0):
        sys.exit()

    get_tweets(api, args.name, num_of_tweets)
    print("[[-]] Success! Tweets retrieved from %s to %s (%s days)\n" %( start_date, end_date, (end_date - start_date).days ))

    print("[[-]] Top 10 Detected Hashtags")
    print_stats(detected_hashtags)
    
    print("[[-]] Top 10 Mentioned Websites")
    print_stats(detected_urls)

    print("[[-]] Top 10 Mentioned Users")
    print_stats(mentioned_users)

    print("[[-]] Top 10 Retweeted Users")
    print_stats(retweeted_users)

    print("[[-]] Top 10 Detected Locations")
    print_stats(detected_locations)

    print("[[-]] Top 10 Detected Devices")
    print_stats(detected_devices)

    utc_offset = args.utc_offset if args.utc_offset else user.utc_offset
    utc_offset = 0 if args.no_timezone else utc_offset
    graph_data(num_of_tweets, utc_offset)



if __name__ == "__main__":
    try:
        main()
    except tweepy.error.TweepError as e:
        print("\nTwitter error: %s" %e)
    except Exception as e:
        print("\nError: %s" %e)
        traceback.print_exc()