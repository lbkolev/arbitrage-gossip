import unittest

from exchanges.binance import Binance
from exchanges.ftx import FTX
from exchanges.bybit import ByBit
from exchanges.huobi import Huobi
from exchanges.kucoin import KuCoin
from exchanges.bitfinex import Bitfinex


class TestExchanges(unittest.IsolatedAsyncioTestCase):
    async def test_binance__check_pair_exists(self):
        self.assertEqual(await Binance("ethusdt")._check_pair_exists(), True)
        self.assertEqual(await Binance("etHusDT")._check_pair_exists(), True)
        self.assertEqual(await Binance("eth-usdt")._check_pair_exists(), False)
        self.assertEqual(await Binance("eth/usdt")._check_pair_exists(), False)

    async def test_ftx__check_pair_exists(self):
        self.assertEqual(await FTX("eth/usdt")._check_pair_exists(), True)
        self.assertEqual(await FTX("eTH/uSDt")._check_pair_exists(), True)
        self.assertEqual(await FTX("eth-usdt")._check_pair_exists(), False)
        self.assertEqual(await FTX("ethusdt")._check_pair_exists(), False)

    async def test_bybit__check_pair_exists(self):
        self.assertEqual(await ByBit("ethusdt")._check_pair_exists(), True)
        self.assertEqual(await ByBit("eTHuSDt")._check_pair_exists(), True)
        self.assertEqual(await ByBit("eth-usdt")._check_pair_exists(), False)
        self.assertEqual(await ByBit("eth/usdt")._check_pair_exists(), False)

    async def test_huobi__check_pair_exists(self):
        self.assertEqual(await Huobi("ethusdt")._check_pair_exists(), True)
        self.assertEqual(await Huobi("eTHuSDt")._check_pair_exists(), True)
        self.assertEqual(await Huobi("eth-usdt")._check_pair_exists(), False)
        self.assertEqual(await Huobi("eth/usdt")._check_pair_exists(), False)

    async def test_kucoin__check_pair_exists(self):
        self.assertEqual(await KuCoin("eth-usdt")._check_pair_exists(), True)
        self.assertEqual(await KuCoin("eTH-uSDt")._check_pair_exists(), True)
        self.assertEqual(await KuCoin("eth/usdt")._check_pair_exists(), False)
        self.assertEqual(await KuCoin("ethusdt")._check_pair_exists(), False)

    async def test_bitfinex__check_pair_exists(self):
        self.assertEqual(await Bitfinex("ETH-USDT")._check_pair_exists(), True)
        self.assertEqual(await Bitfinex("Eth-UsdT")._check_pair_exists(), True)
        self.assertEqual(await Bitfinex("EthUsdT")._check_pair_exists(), True)
        self.assertEqual(await Bitfinex("ETH/USDT")._check_pair_exists(), False)


if __name__ == "__main__":
    unittest.main()
