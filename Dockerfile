FROM python:3.10 AS build

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .
ENV base="btc"
ENV quote="usdt"
ENV report_to="twitter"
ENV threshold="1"
ENV cooldown="300"
ENV log_level="info"
ENV log_file="/dev/null"
ENV TWITTER_API_KEY=${TWITTER_API_KEY}
ENV TWITTER_API_SECRET=${TWITTER_API_SECRET}
ENV TWITTER_ACCESS_TOKEN=${TWITTER_ACCESS_TOKEN}
ENV TWITTER_TOKEN_SECRET=${TWITTER_TOKEN_SECRET}

CMD /usr/local/bin/python arbitrage-gossip/main.py \
  --base=${base} \
  --quote=${quote} \
  --report-to=${report_to} \
  --threshold=${threshold} \
  --cooldown=${cooldown} \
  --log-level=${log_level} \
  --log-file=${log_file}
