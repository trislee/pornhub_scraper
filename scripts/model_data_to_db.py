# -*- coding: UTF-8 -*-

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#

import json
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

from extract_fields import process_number_str

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#

MODEL_FILE = Path('.').resolve().parent/'data'/'models.ndjson'
DB_FILE = 'sqlite:///../data/pornhub.db'

NUMBER_STR_FIELDS = ['Video Views', 'Profile Views', 'Videos Watched']
IGNORE_COLUMNS = [
  'Pornstar Profile Views',
  'Career Start and End',
  'Pornstar Rank',
  'Eye Color',
  'Interests and hobbies']

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#

if __name__ == '__main__':

  # Initialize database connection and read json dump for each model
  #---------------------------------------------------------------------------#

  engine = create_engine(DB_FILE, echo=False)

  with open(MODEL_FILE, 'r') as f:
    lines = filter(None, f.read().split('\n'))
  data = [json.loads(line) for line in lines]

  all_models = []

  # Loop over all model data dicts in the ndjson file
  #---------------------------------------------------------------------------#

  for model in data:

    ranking = model.pop('ranking_dict')
    social = model.pop('social_dict')

    # Convert modelhub key in social dict to standard form
    modelhub_key = None
    modelhub_url = None
    for key, val in social.items():
      if 'modelhub' in key.lower():
        modelhub_url = val
        modelhub_key = key
    if modelhub_key is not None:
      social['Modelhub'] = modelhub_url
      social.pop(modelhub_key)

    info = model.pop('info_dict')

    # Convert number strings in info dict to integers
    for field in NUMBER_STR_FIELDS:
      if field not in info:
        info[field] = 0
      else:
        info[field] = process_number_str(info[field])

    # Combine flat dicts into a single dict
    combined_model = model | social | info | ranking

    all_models.append(combined_model)

  # Convert lists of dicts to DataFrames
  #---------------------------------------------------------------------------#

  df = pd.DataFrame(all_models)
  df = df.drop(IGNORE_COLUMNS, axis = 'columns')

  # Insert the data in the DataFrame to a table in a SQLite database
  #---------------------------------------------------------------------------#

  df.drop_duplicates().to_sql(
    name = 'models',
    con = engine,
    index = False,
    if_exists = 'replace')

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#