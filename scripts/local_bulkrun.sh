#!/bin/bash

if [[ -z "$1" ]];then
    echo -e "Invalid file."
    exit 1
fi

blacklisted=(busd dai hot amp usdc gmt rune rly)

# list of coins
file="$1"
coins=$(awk '{print $1}' $file)

quote="usdt"

for coin in $coins;do
    if [[ "${blacklisted[*]}" =~ "${coin,,}" ]];then
        echo "${coin^^} is blacklisted - skipping"
        continue
    fi

    python arbitrage-gossip/main.py --base $coin --quote $quote --report-to=twitter --cooldown=250 --threshold=1.69 1>/dev/null 2>&1 &
    
    if [[ $? -eq 0 ]];then
        echo "${coin^^}${quote^^} - OK"
    else
        echo "${coin^^}${quote^^} - NOT OK"
    fi
    sleep 1
done
