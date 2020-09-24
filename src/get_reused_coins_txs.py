# This script fetches txs from Blockstream API
# (useful to link a tx input to the previous tx)
# starting from a subset of funding txs.

from utils import get_blockstream_tx, write_json, on_chain_heuristics_list, read_json
from load_data import channels, funding_address_entity, settlement_address_entity, \
    funding_txs, set_mapping

output_dir = '../data/joined/level_1/'
output_file = output_dir + 'chpoints_reusing_coins.json'

# use all on-chain clustering heuristics to have a wider overlap
# then the linking heuristics will decide which triplets to use
och = {h: (True if h != 'none' else False) for h in on_chain_heuristics_list}

funding_address_entity, settlement_address_entity, = \
    set_mapping(funding_address_entity, settlement_address_entity, och)

fes = set(funding_address_entity.values())
ses = set(settlement_address_entity.values())
overlap_entities = fes.intersection(ses)

print('len overlap entities', len(overlap_entities))

useful_chpoints = set()
settlement_entities = settlement_address_entity.values()
for chpoint in channels.chan_point.values:
    hsh, out_index = chpoint.split(':')
    ftx = funding_txs[hsh]
    for inp in ftx['vin']:
        e = funding_address_entity[inp['prevout']['scriptpubkey_address']]
        if e in overlap_entities and e in settlement_entities:
            useful_chpoints.add(chpoint)
            break

print('len useful_chpoints', len(useful_chpoints))

chpoints_reusing_coins = dict()

write_json(list(useful_chpoints), output_file)
