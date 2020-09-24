# This script fetches funding txs from the GraphSense API (access token needed)
# starting from a list of LN channel points.

from utils import write_json
from api_calls import get_tx
import pandas as pd

input_dir = '../data/joined/level_2/'
input_file = input_dir + 'channel.csv'

output_dir = '../data/joined/level_1/'
output_file = output_dir + 'blockstream_funding_txs.json'

channels = pd.read_csv(input_file)

funding_txs = dict()  # key: hash, value: dict with details
for channel in channels.chan_point.values:
    hsh = channel.split(':')[0]
    funding_txs[hsh] = None

fails = 1
while fails:
    fails = 0
    for i, hsh in enumerate(funding_txs):
        # value must be dict and with details
        if not isinstance(funding_txs[hsh], dict) or \
                'height' not in funding_txs[hsh]:
            try:
                print('Fetching funding tx', i, end='\r')
                funding_txs[hsh] = get_tx(hsh)
            except Exception as e:
                fails += 1
                print(e)

write_json(funding_txs, output_file)
