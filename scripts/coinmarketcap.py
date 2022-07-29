import requests
import dotenv
import json
import os
import sys
from datetime import datetime

top = int(sys.argv[1])

PROGRAM_DIR = os.path.dirname(os.path.realpath(__file__)) + "/../"
SCRIPTS_DIR = os.path.dirname(os.path.realpath(__file__))

current_date = datetime.utcnow().strftime("%Y%m%d-%H%M")
url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/map'
dotenv.load_dotenv(PROGRAM_DIR + ".env")
headers = {
    'X-CMC_PRO_API_KEY' : os.environ['COINMARKETCAP_API_KEY']    
}
output_file = f"{SCRIPTS_DIR}/top{top}_{current_date}"

resp = requests.get(url=url, headers=headers)
if resp.status_code == 200:
    val = json.loads(resp.text)
    for coin in val['data']:
        # get top 1000 coins from coinmarketcap
        if int(coin['rank']) < top:
            fd = open(output_file, 'a')
            try:
                #fd.write(f"{coin['symbol']} {coin['rank']}\n")
                fd.write(f"{coin['symbol'].lower()}\n")
                sys.stdout.write(f"Fetched {coin['symbol']} - ranked {coin['rank']}\n")
            except BaseException as e:
                raise e
            finally:
                fd.close()
else:
    print(f"Err {resp.reason}")
