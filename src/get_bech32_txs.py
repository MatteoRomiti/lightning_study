from utils import *
from api_calls import *

onchain_data = read_json('../data/input_output_addresses_all_channels_1580648783')
bech32_addresses = [a for a in onchain_data if a[:2] == 'bc']

address_txs = dict()
for i, a in enumerate(bech32_addresses):
	try:
		print(len(bech32_addresses), i, end='\r')
		address_txs[a] = get_address_txs(a)
	except Exception as e:
		print(e, a)
write_json(address_txs, '../data/bech32_address_txs.json')
