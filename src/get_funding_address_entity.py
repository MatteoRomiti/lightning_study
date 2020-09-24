# This script fetches the entity IDs of funding addresses
# from the GraphSense API (access token needed)
# starting from a list funding txs.

from utils import read_json, write_json, fill_address_entity

from time import sleep

input_dir = '../data/joined/level_1/'
input_file = input_dir + 'blockstream_funding_txs.json'

output_dir = '../data/joined/level_1/'
output_file = output_dir + 'funding_address_entity_september.json'

funding_txs = read_json(input_file)

try:
	funding_address_entity = read_json(output_file)
	print('Reusing data')
except Exception as e:
	funding_address_entity = dict()
	for tx in funding_txs.values():
		for i in tx['inputs']:
			funding_address_entity[i['address']] = None


fails = 1
while fails:
	funding_address_entity, fails = fill_address_entity(funding_address_entity)
	print('Number of fails', fails)
	write_json(funding_address_entity, output_file)
	sleep(5)
