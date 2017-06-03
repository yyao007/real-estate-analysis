#!/bin/bash
source ~/ENV/bin/activate
screen -dmS blog
screen -S blog -p 0 -X stuff $'scrapy crawl blog 2>&1 | tee "$(echo "$(date +%Y-%m-%d).log")" &\r'
