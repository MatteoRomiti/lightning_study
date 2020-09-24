# take all attributed addresses, 
# map them into components, 
# if components are linked to nodes and node has no or useless alias
# link nodes to known entity

from utils import level1_folder, on_chain_heuristics_list, read_json, results_folder
from load_data import node_alias, funding_address_entity, settlement_address_entity, set_mapping
from sort_mapping_entities import relaxed
import pandas as pd

if relaxed:
    results_folder += 'relaxed_filtered_'
else:
    results_folder += 'filtered_'


input_file1 = level1_folder + 'address_categories.csv'
input_file2 = results_folder + 'all_heuristic_1_entity_node.json'
input_file3 = results_folder + 'all_heuristic_2_entity_node_conf.json'

known_addresses = pd.read_csv(input_file1)
entity_nodes_1 = read_json(input_file2, True)
entity_nodes_2 = read_json(input_file3, double_int_key=True)[2]

on_chain_heuristics = {och: (True if och != 'none' else False) for och in on_chain_heuristics_list}

funding_address_entity, settlement_address_entity, = set_mapping(
    funding_address_entity,
    settlement_address_entity,
    on_chain_heuristics)

for entity_node in [entity_nodes_1, entity_nodes_2]:
    known_addresses_nodes = dict()
    linked_nodes = set()
    for address in known_addresses.address:
        if address in funding_address_entity:
            entity = funding_address_entity[address]
            if entity in entity_node:
                nodes = entity_node[entity]
                # print(address, entity, nodes)
                known_addresses_nodes[address] = nodes
                linked_nodes = linked_nodes.union(nodes)
        elif address in settlement_address_entity:
            entity = settlement_address_entity[address]
            if entity in entity_node:
                nodes = entity_node[entity]
                # print(address, entity, nodes)
                known_addresses_nodes[address] = nodes
                linked_nodes = linked_nodes.union(nodes)

    print('number of known addresses linked to nodes', len(known_addresses_nodes))
    print('number of nodes linked to known addresses', len(linked_nodes))
    for node in linked_nodes:
        if node in node_alias:
            print(node_alias[node])