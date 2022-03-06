# -*- coding: UTF-8 -*-

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#

import os
import json

import requests
from bs4 import BeautifulSoup

from extract_fields import get_info

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#

URL_LIST_FILE = '../data/video_urls.txt'

OUTPUT_FILE = '../data/data.ndjson'
ERROR_FILE = '../data/error.log'

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#

if __name__ == '__main__':

  with open( URL_LIST_FILE, 'r' ) as f:
    url_list = sorted(f.read( ).split( '\n' ))

  for i, url in enumerate(url_list):

    print(i, url)

    try:
      n_retries = 0
      r = requests.get(url)

      while (r.status_code != 200) and (n_retries < 5):
        n_retries += 1
        r = requests.get(url)

      if r.status_code != 200:
        message = f'url#: {i}: {url}, unsuccessful request\n'
        with open(ERROR_FILE, 'a') as f:
          f.write(message)
      else:
        soup = BeautifulSoup(r.content, features = 'lxml')
        info = get_info(soup)
        with open(OUTPUT_FILE, 'a') as f:
          f.write(json.dumps(info) + '\n')

    except Exception as e:
      message = f'url#: {i}: {url}, error: {e}\n'
      with open(ERROR_FILE, 'a') as f:
        f.write(message)

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#