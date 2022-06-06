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

        # Get the env. variables
        self.api_key = os.environ["TWITTER_API_KEY"]
        self.api_secret_key = os.environ["TWITTER_API_SECRET_KEY"]
        self.api_access_token = os.environ["TWITTER_ACCESS_TOKEN"]
        self.api_token_secret = os.environ["TWITTER_TOKEN_SECRET"]
        logging.getLogger()

    async def notify(self, pair, prices) -> bool:
        ### Authorization protocol
        auth = tweepy.OAuthHandler(self.api_key, self.api_secret_key)
        auth.set_access_token(self.api_access_token, self.api_token_secret)

        ### Providing access to API
        API = tweepy.API(auth)

        tweet = f"""🏃🏃🏃🏃🏃
PIR: #{pair['merged'].upper()}\n
Exchange with lower price(#{prices['min']['exchange']}):  {prices['min']['price']}
Exchange with higher price(#{prices['max']['exchange']}): {prices['max']['price']}
Pice Difference: {prices['price_diff']} 
Price Difference In %: {prices['price_diff_perc']}
🏃🏃🏃🏃🏃


#cryptocurrencies #crypto #cryptotrading #arbitrager #cryptoarbitrager
"""
        try:
            ### Tweeting to the linked twitter account
            API.update_status(tweet)
            logging.info(
                f"Notified Twitter App with the following data:\nHighest: {prices['max']}\nLowest:{[prices['min']]}"
            )
            self.last_reported = time.time()
            return True
        except tweepy.errors.TweepyException as e:
            logging.error(e)
        return False
