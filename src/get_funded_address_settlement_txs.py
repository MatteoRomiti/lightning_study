# This script fetches settlement txs of funded addresses
# from the GraphSense API (access token needed)
# starting from a list of funding txs and channels
# and create a list of settlement addresses.

from utils import read_json, write_json
from api_calls import get_address_txs, get_tx
import pandas as pd

input_dir_1 = '../data/joined/level_1/'
input_dir_2 = '../data/joined/level_2/'
input_file_1 = input_dir_1 + 'funding_txs.json'
input_file_2 = input_dir_2 + 'channel.csv'

output_dir = '../data/joined/level_1/'
output_file_1 = output_dir + 'funded_address_settlement_txs.json'
output_file_2 = output_dir + 'settlement_addresses.json'
output_file_3 = output_dir + 'settlement_txs.json'

funding_txs = read_json(input_file_1)
channels = pd.read_csv(input_file_2)

funded_address_settlement_txs = dict()
for i, channel in enumerate(channels.chan_point.values):
    hsh, out_index = channel.split(':')
    funded_address = funding_txs[hsh]['outputs'][int(out_index)]['address']
    fund_satoshi = funding_txs[hsh]['outputs'][int(out_index)]['value']['value']
    funded_address_settlement_txs[funded_address] = None

fails = 1
while fails:
    fails = 0
    for i, funded_address in enumerate(funded_address_settlement_txs):
        print('Fetching txs of address', i, end='\r')
        if not isinstance(funded_address_settlement_txs[funded_address], list):
            try:
                txs = get_address_txs(funded_address)
                if len(txs) > 2:
                    # doesn't happen in our dataset
                    print('Address with > 2 settlement txs:', len(txs), funded_address)
                for tx in txs:
                    if tx['value']['value'] < 0: # spending coins
                        d = get_tx(tx['tx_hash'])
                        if 'message' not in d:
                            # not an error
                            funded_address_settlement_txs[funded_address] = []
                            funded_address_settlement_txs[funded_address].append(d)
            except Exception as e:
                fails += 1
                print(e)

settlement_addresses = set()
for fa in funded_address_settlement_txs:
    if funded_address_settlement_txs[fa]:
        for out in funded_address_settlement_txs[fa][0]['outputs']:
            settlement_addresses.add(out['address'])

settlement_txs = []
for stxs in funded_address_settlement_txs.values():
    if stxs:
        settlement_txs.append(stxs[0])

write_json(funded_address_settlement_txs, output_file_1)
write_json(list(settlement_addresses), output_file_2)
write_json(settlement_txs, output_file_3)
