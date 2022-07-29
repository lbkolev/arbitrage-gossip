#!/bin/bash

trap "echo Exited!; exit;" SIGINT SIGTERM

quote="usdt"
cooldown=300
for base in $(cat pairs);do
  if [[ "$base" =~ "eth|btc|xrp|bnb" ]];then
    threshold=1
  else
    threshold=2.50
  fi

  #helm uninstall "${base}${quote}"
  helm install --namespace=arbitrage-gossip "${base}${quote}" ../deploy/arbitrage-gossip-chart \
    --set Pair.base=${base} \
    --set Pair.quote=${quote} \
    --set Pair.threshold=${threshold} \
    --set Pair.cooldown=${cooldown} \
    && sleep 10
  #helm upgrade "${base}${quote}" ../deploy/arbitrage-gossip-chart/ \
  #  --set Pair.base=${base} \
  #  --set Pair.quote=${quote} \
  #  --set Pair.threshold=${threshold} \
  #  --set Pair.cooldown=${cooldown}

done
