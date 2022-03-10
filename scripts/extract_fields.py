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
  s = s.replace(',', '')
  if s.endswith('K'):
    n = int(float(s.split('K')[0]) * 1000)
  elif s.endswith('M'):
    n = int(float(s.split('M')[0]) * 1000000)
  else:
    n = int(s)

  return n

def get_video_info(soup):

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

def get_model_info(soup):

  url = soup.find('link', {'rel' : 'canonical'})['href']
  name = soup.find('h1', {'itemprop' : 'name'}).text.strip()

  cover_image = soup.find('img', {'id' : 'coverPictureDefault'})['src']
  profile_image = soup.find('img', {'id' : 'getAvatar'})['src']

  ranking_info = soup.find('div', {'class' : 'rankingInfo'})
  ranking_keys= [div.text.strip() for div in ranking_info.find_all('div', {'class' : 'title'})]
  ranking_values = [int(span.text.strip().replace('N/A', '-1')) for span in ranking_info.find_all('span', {'class' : 'big'})]
  ranking_dict = dict(zip(ranking_keys, ranking_values))

  views = int(soup.find('div', {'class' : 'videoViews'})['data-title'].split(': ')[-1].replace(',', ''))

  subscribers_soup = [item for item in soup.find_all('div', {'class' : 'tooltipTrig'}) if 'Subscribers' in item.text][0]
  subscribers_str = subscribers_soup['data-title'].split(': ')[-1]
  subscribers = process_number_str(subscribers_str)

  about_items = soup.find('section', {'class' : 'aboutMeSection'}).find_all('div')
  if not about_items:
    about = ''
  else:
    about = about_items[-1].text.strip()

  social_list_soup = soup.find('ul', {'class' : 'socialList'})
  if social_list_soup is None:
    social_dict = {}
  else:
    social_list = social_list_soup.find_all('li')
    social_dict = {item.text.strip() : item.find('a')['href'] for item in social_list}

  info_list = soup.find('div', {'class' : 'js-infoText'}).find_all('div', {'class' : 'infoPiece'})
  info_keys = [item.find('span').text.strip().strip(':') for item in info_list]
  info_values = [item.find('span', {'class' : 'smallInfo'}).text.strip() for item in info_list]
  info_dict = dict(zip(info_keys, info_values))

  if 'doesn\'t have any videos yet.' in soup.text:
    number_videos = 0
  else:
    number_videos = int(soup.find('div', {'class' : 'showingCounter'}).text.split('of')[-1].strip())

  return {
    'url' : url,
    'name' : name,
    'cover_image' : cover_image,
    'profile_image' : profile_image,
    'ranking_dict' : ranking_dict,
    'views' : views,
    'subscribers' : subscribers,
    'about' : about,
    'social_dict' : social_dict,
    'info_dict' : info_dict,
    'number_videos' : number_videos}

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