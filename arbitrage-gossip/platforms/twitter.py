import tweepy
import tweepy.errors
import os
import sys
import logging
import time

from platforms.base import BasePlatform


class Twitter(BasePlatform):
    """Class responsible for notifying the twitter platform"""

    def __init__(self, cooldown):
        super().__init__(cooldown)

        """ Number of retries to attempt when an api connection error occurs"""
        self.retry_count = 5

        """ Number of seconds to wait between retries """
        self.retry_delay = 2

        # Get the credentials from the environment variables
        self.api_key = os.environ["TWITTER_API_KEY"]
        self.api_secret_key = os.environ["TWITTER_API_SECRET_KEY"]
        self.api_access_token = os.environ["TWITTER_ACCESS_TOKEN"]
        self.api_token_secret = os.environ["TWITTER_TOKEN_SECRET"]

        self.conn = self.authorize()

    def authorize(self):
        """authorize with the twitter API."""

        # Authorization protocol
        auth = tweepy.OAuth1UserHandler(
            consumer_key=self.api_key,
            consumer_secret=self.api_secret_key,
            access_token=self.api_access_token,
            access_token_secret=self.api_token_secret,
        )

        # Providing access to API
        try:
            conn = tweepy.API(auth)
            logging.info("Established connection with twitter.")
            return conn
        except BaseException as e:
            logging.error(e)
            sys.exit(1)

    async def notify(self, pair, prices) -> bool:
        """Notify the twitter platform."""

        tweet = f"""🏃🏃🏃🏃🏃
PAIR: #{pair['merged'].upper()}\n
Exchange with lowest price(#{prices['min']['exchange']}):  {prices['min']['price']}
Exchange with highest price(#{prices['max']['exchange']}): {prices['max']['price']}
Price Difference: {prices['price_diff']} 
Price Difference In %: {prices['price_diff_perc']}
🏃🏃🏃🏃🏃


#cryptocurrencies #crypto #trading #arbitrager #bot
"""
        try:
            # Tweet to the linked twitter account
            self.conn.update_status(tweet)
            logging.info(
                f"Notified Twitter App with the following data:\nHighest: {prices['max']}\nLowest:{[prices['min']]}"
            )
            self.last_reported = time.time()
            return True
        except tweepy.errors.TweepyException as e:
            logging.error(f"{self.platform} {str(e)}")
