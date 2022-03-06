# -*- coding: UTF-8 -*-

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#

import json
from datetime import datetime

import requests
from bs4 import BeautifulSoup

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#

COMMENT_API_URL = 'https://www.pornhub.com/comment/show'

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#

def process_number_str(s):
  if s.endswith('K'):
    n = int(float(s.split('K')[0]) * 1000)
  elif s.endswith('M'):
    n = int(float(s.split('M')[0]) * 1000000)
  else:
    n = int(s)

  return n

def get_info(soup):

  metadata_soup = soup.find('script', {'type' : 'application/ld+json'})
  if metadata_soup is not None:
    metadata = json.loads(metadata_soup.text.replace('\t', ''))
    date = datetime.fromisoformat(metadata['uploadDate'])
    views_str = [val['userInteractionCount'] for val in metadata['interactionStatistic'] if val['interactionType'] == 'http://schema.org/WatchAction'][0]
    views = int(views_str.replace(',', ''))
  else:
    date, views = metadata_alternative(soup = soup)

  detailed_info = soup.find('div', {'class' : 'video-detailed-info'})

  categories = process_wrapper(detailed_info, 'categoriesWrapper')
  tags = process_wrapper(detailed_info, 'tagsWrapper')
  pornstars = process_wrapper(detailed_info, 'pornstarsWrapper')
  related_terms = process_wrapper(detailed_info, 'relatedSearchTermsContainer')
  production = process_wrapper(detailed_info, 'productionWrapper')

  url = soup.find('meta', {'property' : 'og:url'})['content']
  title = soup.find('h1', {'class' : 'title'}).text.strip()
  video_id = int(soup.find('div', {'class' : 'mainPlayerDiv'})['data-video-id'])

  embed_url = soup.find('meta', {'property' : 'og:video:url'})['content']
  thumbnail_url = soup.find('meta', {'property' : 'og:image'})['content']
  duration = int(soup.find('meta', {'property' : 'video:duration'})['content'])

  percent = int(soup.find('span', {'class' : 'percent'}).text.strip('%'))
  upvotes = int(soup.find('span', {'class' : 'votesUp'})['data-rating'])
  downvotes = int(soup.find('span', {'class' : 'votesDown'})['data-rating'])
  favorites_str = soup.find('span', {'class' : 'favoritesCounter'}).text.strip()
  favorites = process_number_str(favorites_str)

  uploader_info_soup = soup.find('div', {'class' : 'video-info-row userRow'}).find('div', {'class' : 'userInfo'})
  if uploader_info_soup.find('a', href = True) is not None:
    uploader_info = uploader_info_soup.find('a', href = True)
    uploader_link = uploader_info['href']
    uploader_name = uploader_info.text.strip()
  else:
    uploader_link = None
    uploader_name = uploader_info_soup.find('span', {'class' : 'username'}).text

  comments = get_comments_from_soup(soup = soup, video_id = video_id)
  if len([ c for c in comments if c['parent_id'] is None]) >= 200:
    all_comments = get_all_comments(video_id = video_id)
  else:
    all_comments = comments

  return {
    'url' : url,
    'title' : title,
    'tags' : tags,
    'categories' : categories,
    'video_id' : video_id,
    'embed_url' : embed_url,
    'thumbnail_url' : thumbnail_url,
    'duration' : duration,
    'timestamp' : date.timestamp(),
    'views' : views,
    'percent' : percent,
    'upvotes' : upvotes,
    'downvotes' : downvotes,
    'favorites' : favorites,
    'pornstars' : pornstars,
    'production' : production,
    'related_terms' : related_terms,
    'uploader_link' : uploader_link,
    'uploader_name' : uploader_name,
    'comments' : all_comments}

def metadata_alternative(soup):

  og_image_url = soup.find('meta', {'property' : 'og:image'})['content']

  yearmonth, day = og_image_url.split('videos/')[1].split('/')[:2]
  day = int(day)
  year = int(yearmonth[:4])
  month = int(yearmonth[-2:])
  date = datetime(year = year, month = month, day = day)

  views = process_number_str(soup.find('div', {'class' : 'views'}).find('span').text)

  return date, views

def process_wrapper(detailed_info_soup, class_name):

  wrapper_soup = detailed_info_soup.find('div', {'class' : class_name})

  # only `tags`` and `related terms` wrappers are allowed to be empty`
  if (wrapper_soup is None) and (class_name in ['relatedSearchTermsContainer', 'tagsWrapper']):
    return []

  wrapper_items = wrapper_soup.find_all('a', href = True)

  return [{
    'text': wrapper_item.text.strip(),
    'link': wrapper_item.get('href') } for wrapper_item in wrapper_items]

def get_comment_parent_id(nested_block):
  return int([c for c in nested_block.attrs['class'] if c.startswith('childrenOf')][0].split('childrenOf')[-1])

def process_comment(comment_block, video_id, parent_id = None):

  if comment_block.find('div', {'class' : 'date'}).text == '[[dateAdd]]':
    return None

  user_soup = comment_block.find('a', {'class' : 'userLink'}, href = True)
  if user_soup is None:
    user_link = None
  else:
    user_link = user_soup['href']

  user_image = comment_block.find('img')['data-src']
  date = comment_block.find('div', {'class' : 'date'}).text.strip()
  votes = int(comment_block.find('span', {'class' : 'voteTotal'}).text)
  message = comment_block.find('div', {'class' : 'commentMessage'}).find('span').text

  comment_id = int([c for c in comment_block.attrs['class'] if c.startswith('commentTag')][0].split('commentTag')[-1])

  return {
    'user_link' : user_link,
    'user_image' : user_image,
    'date' : date,
    'votes' : votes,
    'message' : message,
    'video_id' : video_id,
    'comment_id' : comment_id,
    'parent_id' : parent_id}

def get_comments_from_soup(soup, video_id):

  comments = []

  nested_blocks = soup.find_all('div', {'class' : 'nestedBlock'})

  for nested_block in nested_blocks:
    parent_id = get_comment_parent_id(nested_block)
    comment_blocks = nested_block.find_all('div', {'class' : 'commentBlock'})
    for comment_block in comment_blocks:
      comments.append(process_comment(comment_block = comment_block, video_id = video_id, parent_id = parent_id))
    nested_block.decompose()

  comment_blocks = soup.find_all('div', {'class' : 'commentBlock'})

  for comment_block in comment_blocks:
    comments.append(process_comment(comment_block = comment_block, video_id = video_id, parent_id = None))

  return list(filter(None, comments))

def get_comments(video_id, page):

  params = {
    'id': video_id,
    'limit': 200,
    'popular': 1,
    'what': 'video',
    'page': page,}

  r = requests.get(COMMENT_API_URL, params = params)
  soup = BeautifulSoup(r.content, features = 'lxml')

  return get_comments_from_soup(soup = soup, video_id = video_id)

def get_all_comments(video_id):

  page = 1
  all_comments = []

  while True:
    comments = get_comments(video_id = video_id, page = page)
    if len(comments) == 0:
      break
    else:
      all_comments.extend(comments)
      page += 1

  return all_comments