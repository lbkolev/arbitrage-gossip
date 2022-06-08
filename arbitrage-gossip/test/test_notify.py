import unittest
import dotenv
import os

from platforms.twitter import Twitter

class TestPlatforms(unittest.IsolatedAsyncioTestCase):
    async def test_twitter_connectivity(self):
        dotenv.load_dotenv(os.path.dirname(os.path.realpath(__file__)) + "/../../.env")
        self.assertNotEqual(Twitter(15).authorize(), False)


if __name__ == "__main__":
    unittest.main()
