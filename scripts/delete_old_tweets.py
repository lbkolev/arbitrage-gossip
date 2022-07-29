import tweepy
import dotenv
import os
import sys
import time
from datetime import datetime, timedelta

if __name__ == "__main__":
    tweets_to_save = [
        #573245340398170114, # keybase proof
        #573395137637662721, # a tweet to this very post
    ]

        
    # auth and api
    dotenv.load_dotenv('.env')
    auth = tweepy.OAuth1UserHandler(
            consumer_key=os.environ['TWITTER_API_KEY'],
            consumer_secret=os.environ['TWITTER_API_SECRET_KEY'],
            access_token=os.environ['TWITTER_ACCESS_TOKEN'],
            access_token_secret=os.environ['TWITTER_TOKEN_SECRET'],
            )


    time_now = time.time()
    delete_before = timedelta(0).total_seconds()
    delete_after = timedelta(5000).total_seconds()

    # get all timeline tweets
    deletion_count = 0
    ignored_count = 0

    # delete old tweets
    # for many tweets we get terminated, hence the loop
    while True:
        api = tweepy.API(auth)

        print("Retrieving timeline tweets")
        timeline = tweepy.Cursor(api.user_timeline).items()
        for tweet in timeline:
            tweet_time = datetime.timestamp(tweet.created_at)
            print(f"Currently at tweet {tweet.id}")
            # format of twitter api dates:
            # Sun Mar 20 10:06:48 +0000 2022
            #tweet_time = time.mktime(time.strptime(tweet.created_at, '%a %b %d %H:%M:%S +0000 %Y'))
            if tweet.id not in tweets_to_save and tweet_time + delete_before < time_now and tweet_time + delete_after > time_now:
                print(f"Deleting {tweet.id}: {tweet.created_at} {tweet.text}")
                api.destroy_status(tweet.id) 
                deletion_count += 1
            else:
                print(f"Skipping {tweet.id}: {tweet.created_at} {tweet.text}")
                ignored_count += 1
        print(f"Deleted {deletion_count} tweets, ignored {ignored_count}")
