# -*- coding: UTF-8 -*-

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#

import os
import json
import logging
import random

import requests
from bs4 import BeautifulSoup

from extract_fields import get_info

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#

URL_LIST_FILE = '../data/video_urls_02.txt'

OUTPUT_FILE = '../data/data.ndjson'
LOG_FILE = '../data/scraper.log'

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#

if __name__ == '__main__':

  # Initialize logger in "append" mode
  logging.basicConfig(
    filename = LOG_FILE,
    filemode = 'a',
    level = logging.INFO,
    format='TIME: %(created)f | %(message)s')

  logger = logging.getLogger(__name__)

  # Read in list of URLs to process
  with open( URL_LIST_FILE, 'r' ) as f:
    url_list = list(filter(None, sorted(f.read( ).split( '\n' ))))

  # If the output file contains previously-generated data, ignore
  # previously-processed URLs
  if os.path.isfile(OUTPUT_FILE):
      with open(OUTPUT_FILE, 'r') as f:
        lines = list(filter(None, f.read().split('\n')))
      completed_urls = [json.loads(line)['url'] for line in lines]

      url_list = list(set(url_list) - set(completed_urls))

  # Shuffle URL list order to avoid a making lot of failed requests at the
  # beginning of the program, which can trigger remote disconnection issues
  url_list = random.shuffle(url_list)

  # Loop over URLs, download and process data from page of each URL
  #---------------------------------------------------------------------------#

  for i, url in enumerate(url_list):

    try:

      # Make up to 5 attempts to retrieve content from a given URL
      n_retries = 0
      r = requests.get(url)

      while (r.status_code != 200) and (n_retries < 5):
        n_retries += 1
        r = requests.get(url)

      if r.status_code != 200:
        # If all 5 attempts failed
        logger.info(f'URL#: {i} | URL: {url} | STATUS: failed | DETAIL: request failed')

      else:
        # Content from the given URL was retrieved, so can be processed
        soup = BeautifulSoup(r.content, features = 'lxml')
        info = get_info(soup)

        # Write JSON-serialized dict of all data from the video as a line in the
        # output ndjson file
        with open(OUTPUT_FILE, 'a') as f:
          f.write(json.dumps(info) + '\n')
        logger.info(f'URL#: {i} | URL: {url} | STATUS: success | DETAIL: None')

    except Exception as e:
      # Some error was encountered during the request for or parsing of content
      logger.info(f'URL#: {i} | URL: {url} | STATUS: failed | DETAIL: {e}')

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#