# -*- coding: UTF-8 -*-

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#

import json
import logging

import requests
from bs4 import BeautifulSoup

from extract_fields import get_info

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#

URL_LIST_FILE = '../data/video_urls_02.txt'

OUTPUT_FILE = '../data/data.ndjson'
LOG_FILE = '../data/scraper.log'

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#

if __name__ == '__main__':

  logging.basicConfig(
    filename = LOG_FILE,
    level = logging.INFO,
    format='TIME: %(created)d | %(message)s')

  logger = logging.getLogger(__name__)

  with open( URL_LIST_FILE, 'r' ) as f:
    url_list = list(filter(None, sorted(f.read( ).split( '\n' ))))

  for i, url in enumerate(url_list):

    try:
      n_retries = 0
      r = requests.get(url)

      while (r.status_code != 200) and (n_retries < 5):
        n_retries += 1
        r = requests.get(url)

      if r.status_code != 200:
        logger.info(f'URL#: {i} | URL: {url} | STATUS: failed | DETAIL: request failed')
      else:
        soup = BeautifulSoup(r.content, features = 'lxml')
        info = get_info(soup)
        with open(OUTPUT_FILE, 'a') as f:
          f.write(json.dumps(info) + '\n')
        logger.info(f'URL#: {i} | URL: {url} | STATUS: success | DETAIL: None')

    except Exception as e:
      logger.info(f'URL#: {i} | URL: {url} | STATUS: failed | DETAIL: {e}')

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#