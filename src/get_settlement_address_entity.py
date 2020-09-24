# This script fetches the entity IDs of settlement addresses
# from the GraphSense API (access token needed)
# starting from a list of settlement addresses.

from utils import read_json, write_json, fill_address_entity

from time import sleep

input_dir = '../data/joined/level_1/'
input_file = input_dir + 'settlement_addresses.json'

output_dir = '../data/joined/level_1/'
output_file = output_dir + 'settlement_address_entity_september.json'

settlement_addresses = read_json(input_file)

try:
    settlement_address_entity = read_json(output_file)
    print('Reusing data')
except Exception as e:
    settlement_address_entity = dict()
    for sa in settlement_addresses:
        settlement_address_entity[sa] = None

fails = 1
while fails:
    settlement_address_entity, fails = fill_address_entity(settlement_address_entity)
    print('Number of fails', fails)
    write_json(settlement_address_entity, output_file)
    sleep(5)
