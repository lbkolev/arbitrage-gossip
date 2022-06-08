#!/bin/bash

base=(btc eth bnb luna doge shib ftt sol xrp ada op matic)
quote='usdt'

for asset in ${base[@]};do
    if [[ $asset == "luna" ]]; then
        python arbitrage-gossip/main.py --base $asset --quote $quote --report-to=twitter --cooldown=150 --threshold=1 > /dev/null 2>&1 &
    else
        python arbitrage-gossip/main.py --base $asset --quote $quote --report-to=twitter --cooldown=150 --threshold=0.2 > /dev/null 2>&1 &
    fi

    if [[ $? -eq 0 ]];then
        echo "${asset^^}${quote^^} - OK"
    else
        echo "${asset^^}${quote^^} - NOT OK"
    fi
done

#python arbitrage-gossip/main.py --base luna  --quote usdt --report-to=twitter --cooldown=150 --threshold=1   > /dev/null 2>&1 &
#python arbitrage-gossip/main.py --base bnb   --quote usdt --report-to=twitter --cooldown=150 --threshold=0.2 > /dev/null 2>&1 &
#python arbitrage-gossip/main.py --base btc   --quote usdt --report-to=twitter --cooldown=150 --threshold=0.2 > /dev/null 2>&1 &
#python arbitrage-gossip/main.py --base eth   --quote usdt --report-to=twitter --cooldown=150 --threshold=0.2 > /dev/null 2>&1 &
#python arbitrage-gossip/main.py --base doge  --quote usdt --report-to=twitter --cooldown=150 --threshold=0.2 > /dev/null 2>&1 &
#python arbitrage-gossip/main.py --base shib  --quote usdt --report-to=twitter --cooldown=150 --threshold=0.2 > /dev/null 2>&1 &
#python arbitrage-gossip/main.py --base ftt   --quote usdt --report-to=twitter --cooldown=150 --threshold=0.2 > /dev/null 2>&1 &
#python arbitrage-gossip/main.py --base sol   --quote usdt --report-to=twitter --cooldown=150 --threshold=0.2 > /dev/null 2>&1 &
#python arbitrage-gossip/main.py --base xrp   --quote usdt --report-to=twitter --cooldown=150 --threshold=0.2 > /dev/null 2>&1 &
#python arbitrage-gossip/main.py --base ada   --quote usdt --report-to=twitter --cooldown=150 --threshold=0.2 > /dev/null 2>&1 &
#python arbitrage-gossip/main.py --base op    --quote usdt --report-to=twitter --cooldown=150 --threshold=0.2 > /dev/null 2>&1 &
#python arbitrage-gossip/main.py --base matic --quote usdt --report-to=twitter --cooldown=150 --threshold=0.2 > /dev/null 2>&1 &
