import unittest

from exchanges.binance import Binance
from exchanges.ftx import FTX
from exchanges.bybit import ByBit
from exchanges.huobi import Huobi
from exchanges.kucoin import KuCoin

class TestExchanges(unittest.IsolatedAsyncioTestCase):

    async def test_binance_check_pair_exists(self):
        self.assertEqual(await Binance('ethusdt').check_pair_exists(), True)
        self.assertEqual(await Binance('etHusDT').check_pair_exists(), True)
        self.assertEqual(await Binance('eth-usdt').check_pair_exists(), False)
        self.assertEqual(await Binance('eth/usdt').check_pair_exists(), False)

    async def test_ftx_check_pair_exists(self):
        self.assertEqual(await FTX('eth/usdt').check_pair_exists(), True)
        self.assertEqual(await FTX('eTH/uSDt').check_pair_exists(), True)
        self.assertEqual(await FTX('eth-usdt').check_pair_exists(), False)
        self.assertEqual(await FTX('ethusdt').check_pair_exists(), False)

    async def test_bybit_check_pair_exists(self):
        self.assertEqual(await ByBit('ethusdt').check_pair_exists(), True)
        self.assertEqual(await ByBit('eTHuSDt').check_pair_exists(), True)
        self.assertEqual(await ByBit('eth-usdt').check_pair_exists(), False)
        self.assertEqual(await ByBit('eth/usdt').check_pair_exists(), False)

    async def test_huobi_check_pair_exists(self):
        self.assertEqual(await Huobi('ethusdt').check_pair_exists(), True)
        self.assertEqual(await Huobi('eTHuSDt').check_pair_exists(), True)
        self.assertEqual(await Huobi('eth-usdt').check_pair_exists(), False)
        self.assertEqual(await Huobi('eth/usdt').check_pair_exists(), False)

    async def test_kucoin_check_pair_exists(self):
        self.assertEqual(await KuCoin('eth-usdt').check_pair_exists(), True)
        self.assertEqual(await KuCoin('eTH-uSDt').check_pair_exists(), True)
        self.assertEqual(await KuCoin('eth/usdt').check_pair_exists(), False)
        self.assertEqual(await KuCoin('ethusdt').check_pair_exists(), False)


if __name__ == "__main__":
    unittest.main()
