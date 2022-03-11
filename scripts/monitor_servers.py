# -*- coding: UTF-8 -*-

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#

import os
from pathlib import Path
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#

PEM_FILE = '~/.aws/pornhub.pem'

LOG_PATH = '/home/ubuntu/pornhub_scraper/data/scraper.log'
DATA_PATH = '/home/ubuntu/pornhub_scraper/data/data.ndjson'

IP_ADDRESS_LIST = '../../ec2_ip_list.txt'
OUTPUT_DIR = Path('../data', 'logs')

STATUS_DICT = {
  'success' : 1.0,
  'failed' : 0.0}

COPY_DATA = False

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#

def log_to_df(log_file):

  with open(log_file, 'r') as f:
    lines = list(filter(None, f.read().split('\n')))

  row_list = []

  for line in lines:
    keyvals = [keyval.strip() for keyval in line.split('|')]
    row = dict([tuple(keyval.split(': '))[:2] for keyval in keyvals])
    row_list.append(row)

  df = pd.DataFrame(row_list)
  df['TIME'] = df['TIME'].astype(float)
  df['ELAPSED_TIME'] = df['TIME'].diff()
  df['URL#'] = df['URL#'].astype(int)
  df['SUCCESS'] = df['STATUS'].map(STATUS_DICT)

  return df

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#

if __name__ == '__main__':

  with open(IP_ADDRESS_LIST, 'r') as f:
    ip_address_list = list(filter(None, f.read().split('\n')))

  time_str = datetime.now().strftime('%Y%m%d_%H%M%S')
  output_subdir = OUTPUT_DIR/time_str
  os.makedirs(output_subdir, exist_ok = True)

  for i, ip_address in enumerate(ip_address_list):

    output_file = output_subdir/f'scraper_{i:02d}.txt'
    scp_command = f'scp -i {PEM_FILE} ubuntu@{ip_address}:{LOG_PATH} {output_file}'
    os.system(scp_command)

    if COPY_DATA:
      output_file = output_subdir/f'data_{i:02d}.ndjson'
      scp_command = f'scp -i {PEM_FILE} ubuntu@{ip_address}:{DATA_PATH} {output_file}'
      os.system(scp_command)

  #---------------------------------------------------------------------------#

  fig, ax = plt.subplots(1, 2, figsize = (16, 6))

  for i, ip_address in enumerate(ip_address_list):

    output_file = output_subdir/f'scraper_{i:02d}.txt'

    df = log_to_df(output_file)

    rdf = df[['TIME', 'ELAPSED_TIME', 'SUCCESS']].rolling(window = 100, center = True).mean()

    uptime = df['TIME'] - df['TIME'].min()

    ax[0].plot(uptime, rdf['SUCCESS'] * 100, alpha = 0.5, label = i)
    ax[0].set_ylim(-5, 105)
    ax[0].set_xlabel('Uptime [seconds]')
    ax[0].set_ylabel('Success Rate [percentage]')

    ax[1].plot(uptime, rdf['ELAPSED_TIME'], alpha = 0.5, label = i)
    ax[1].set_xlabel('Uptime [seconds]')
    ax[1].set_ylabel('Time per URL [seconds]')

  ax[1].legend(loc = 0)

  plt.savefig(output_subdir.with_suffix('.pdf'), bbox_inches = 'tight')

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#