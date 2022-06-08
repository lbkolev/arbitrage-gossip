import tweepy, tweepy.errors
import logging
import time
import os

from notify.base import BaseNotify


class Twitter(BaseNotify):
    """Class responsible for notifying the twitter platform."""

    """The time of the last report."""
    last_reported = 0

    def __init__(self, cooldown):
        """Report every cooldown seconds."""
        self.cooldown = cooldown

        """Number of retries to attempt when an api connection error occurs."""
        self.retry_count = 5

        """Number of seconds to wait between retries."""
        self.retry_delay = 2

        """ The platform's name."""
        self.platform = self.__class__.__name__

        # Get the env. variables
        self.api_key = os.environ["TWITTER_API_KEY"]
        self.api_secret_key = os.environ["TWITTER_API_SECRET_KEY"]
        self.api_access_token = os.environ["TWITTER_ACCESS_TOKEN"]
        self.api_token_secret = os.environ["TWITTER_TOKEN_SECRET"]
        logging.getLogger()

        self.conn = self.authorize()


    def authorize(self):
        """authorize with the twitter API."""

        ### Authorization protocol
        auth = tweepy.OAuth1UserHandler(consumer_key=self.api_key,
            consumer_secret=self.api_secret_key,
            access_token=self.api_access_token,
            access_token_secret=self.api_token_secret)

        ### Providing access to API
        try: 
            conn = tweepy.API(auth)
            logging.info('Established connection with twitter.')
            return conn
        except BaseException as e:
            logging.error(e)
            return False


    async def notify(self, pair, prices) -> bool:
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
            ### Tweeting to the linked twitter account
            self.conn.update_status(tweet)
            logging.info(
                f"Notified Twitter App with the following data:\nHighest: {prices['max']}\nLowest:{[prices['min']]}"
            )
            self.last_reported = time.time()
            return True
        except tweepy.errors.TweepyException as e:
            logging.error(f"{self.platform} {str(e)}")