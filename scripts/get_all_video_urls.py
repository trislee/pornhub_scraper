# -*- coding: UTF-8 -*-

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#

import requests
from bs4 import BeautifulSoup

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#

SITEMAP_URL = 'https://www.pornhub.com/sitemaps.xml'

OUTPUT_FILE = '../data/all_video_urls.txt'

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#

if __name__ == '__main__':

  r = requests.get(SITEMAP_URL)
  soup = BeautifulSoup(r.content, features = 'lxml')
  sitemap_urls = [loc.text for loc in soup.find_all('loc') if 'sitemap_g_vids' in loc.text]

  #---------------------------------------------------------------------------#

  all_video_urls = []
  for i, sitemap_url in enumerate(sitemap_urls):

    n_retries = 0

    print(i)

    r = requests.get(sitemap_url)

    if (r.status_code) != 200 & (n_retries <  10):
      n_retries += 1
      r = requests.get(sitemap_url)

    soup = BeautifulSoup(r.content, features = 'lxml')
    all_video_urls.extend([loc.text for loc in soup.find_all('loc')])

  #---------------------------------------------------------------------------#

  with open(OUTPUT_FILE, 'w') as f:
    f.write('\n'.join(all_video_urls))

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#