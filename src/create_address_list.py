# create one csv with funding and settlement addresses

from utils import read_json, write_json
import pandas as pd
input_dir = '../data/joined/level_1/'
input_file_1 = input_dir + 'settlement_addresses.json'
input_file_2 = input_dir + 'blockstream_funding_txs.json'

output_dir = '../data/joined/level_1/'
output_file_1 = output_dir + 'addresses.json'
output_file_2 = output_dir + 'addresses.csv'

settlement_addresses = set(read_json(input_file_1))
funding_txs = read_json(input_file_2)
# funding_addresses = set()
for tx in funding_txs.values():
    for i in tx['inputs']:
        settlement_addresses.add(i['address'])

settlement_addresses = [e for e in settlement_addresses]
print(len(settlement_addresses))

addresses_df = pd.DataFrame(settlement_addresses, columns=['address'])
addresses_df.to_csv(output_file_2, index=False)
# write_json(settlement_addresses, output_file_1)

