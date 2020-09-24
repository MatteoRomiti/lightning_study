# This scripts creates a list of funding_node,channel
# based on the linking results

from utils import results_folder, read_json, write_json, on_chain_heuristics_list
from load_data import channels, funding_txs, set_mapping, funding_address_entity, settlement_address_entity
from sort_mapping_entities import relaxed
import pandas as pd


output_file = results_folder + 'funding_node_channel.csv'

if relaxed:
    results_folder += 'relaxed_filtered_'
else:
    results_folder += 'filtered_'

input_file = results_folder + 'all_heuristic_2_entity_node_conf.json'

# get correct address-entity mapping: all
och = on_chain_heuristics = {och: (True if och != 'none' else False) for och in on_chain_heuristics_list}
funding_address_entity, settlement_address_entity, = \
    set_mapping(funding_address_entity, settlement_address_entity, och)

# get linked entities
entity_nodes = read_json(input_file, double_int_key=True)[2]

funding_node_channel = []
# for each funding tx
for channel in channels.values:
    funding_tx, out_index = channel[0].split(':')
    n1, n2 = channel[1], channel[2]
    address = funding_txs[funding_tx]['vin'][0]['prevout']['scriptpubkey_address']
    funding_entity = funding_address_entity[address]
    # if its funding entity is linked to a node
    if funding_entity in entity_nodes:
        # if only one node in the channel is linked to the funding entity
        to_assign = []
        if n1 in entity_nodes[funding_entity]:
            to_assign.append(n1)
        if n2 in entity_nodes[funding_entity]:
            to_assign.append(n1)
        if len(to_assign) == 1:
            funding_node_channel.append([to_assign[0], channel[0]])

columns = ['funding_node', 'channel']
funding_node_channel_df = pd.DataFrame(funding_node_channel, columns=columns)
funding_node_channel_df.to_csv(output_file, index=False)

# problems:
    # what if a funding entity is linked to both nodes in channel?
    # discard channel

# no
# if both nodes are linked
    # if one node is linked to a funding entity and
    # the other node is linked to a non-funding entity