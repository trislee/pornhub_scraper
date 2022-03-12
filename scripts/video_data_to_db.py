# -*- coding: UTF-8 -*-

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#

import os
import json
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#

DATA_DIR = Path('.').resolve().parent/'data'/'video_data'
DB_FILE = 'sqlite:///../data/pornhub.db'

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#

if __name__ == '__main__':

  # Initialize database connection and get list of ndjson raw data files
  #---------------------------------------------------------------------------#

  engine = create_engine(DB_FILE, echo=False)

  _ndjson_files = os.listdir(DATA_DIR)
  ndjson_files = sorted([f for f in _ndjson_files if f.endswith('.ndjson')])

  # Loop over all ndjson raw data files, read json dump for each video
  #---------------------------------------------------------------------------#

  for file in ndjson_files:
    print(file)
    with open(os.path.join(DATA_DIR, file), 'r') as f:
      lines = filter(None, f.read().split('\n'))
    data = [json.loads(line) for line in lines]
    data = [video for video in data if video.get('failed') is None]

    # Initialize empty lists to store data for each table
    #.........................................................................#

    all_categories = []
    all_tags = []
    all_related_terms = []
    all_pornstars = []
    all_comments = []
    all_videos = []

    # Loop over all video data dicts in the ndjson file
    #.........................................................................#

    for video in data:
      video_id = video['video_id']

      # Convert nested dict for each video into multiple flat dicts
      #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#

      _tags = video.pop('tags')
      _categories = video.pop('categories')
      _related_terms = video.pop('related_terms')
      _pornstars = video.pop('pornstars')

      if video['production']:
        video['production'] = video['production'][0]['link']
      else:
        video['production'] = None

      comments = video.pop('comments')

      # Add key-value par of video ID to newly-created flat dicts
      #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#


      categories = [item | {'video_id' : video_id} for item in _categories]
      tags = [item | {'video_id' : video_id} for item in _tags]
      related_terms = [item | {'video_id' : video_id} for item in _related_terms]
      pornstars = [item | {'video_id' : video_id} for item in _pornstars]

      # Extend list of flat dicts for each table
      #. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#

      all_categories.extend(categories)
      all_tags.extend(tags)
      all_related_terms.extend(related_terms)
      all_pornstars.extend(pornstars)
      all_comments.extend(comments)

      all_videos.append(video)

    # Convert lists of dicts to DataFrames
    #.........................................................................#

    cdf = pd.DataFrame(all_categories)
    tdf = pd.DataFrame(all_tags)
    rtdf = pd.DataFrame(all_related_terms)
    pdf = pd.DataFrame(all_pornstars)

    cmdf = pd.DataFrame(all_comments)
    vdf = pd.DataFrame(all_videos)
    vdf['datetime'] = pd.to_datetime(vdf['timestamp'], unit = 's').apply(lambda s : s.to_pydatetime())

    # Append the data in each DataFrame to tables in a SQLite database
    #.........................................................................#

    for table, df in zip(
        ['videos', 'comments', 'categories', 'tags', 'related_terms', 'pornstars'],
        [vdf, cmdf, cdf, tdf, rtdf, pdf]):

      df.drop_duplicates().to_sql(
        name = table,
        con = engine,
        index = False,
        if_exists = 'append')

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#