#!/bin/bash
source ~/ENV/bin/activate
export http_proxy=d09.cs.ucr.edu:3128
export https_proxy=d09.cs.ucr.edu:3128
screen -dmS forum
screen -S forum -p 0 -X stuff $'scrapy crawl forum 2>&1 | tee "$(echo "$(date +%Y-%m-%d).log")" &\r'
