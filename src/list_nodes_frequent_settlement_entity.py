# This script creates a list of nodes associated to the entities that appear the most
# in settlement txs
from utils import read_json, level2_folder, results_folder, on_chain_heuristics_list, write_json
from load_data import settlement_txs, funding_address_entity, settlement_address_entity, set_mapping

# read entity_node from best linking results
results_folder += 'filtered_'
input_file_1 = results_folder + 'all_heuristic_2_entity_node_conf.json'
input_file_2 = level2_folder + 'inactive_selected_nodes.json'
output_file_1 = results_folder + 'nodes_for_ground_truth.json'
# output_file_1 = results_folder + 'nodes_for_ground_truth.json'
entity_node = read_json(input_file_1, double_int_key=True)[2]
inactive_nodes = read_json(input_file_2)

# count how many times an entity appears in a settlement tx
# map addresses in settlement txs to components
on_chain_heuristics = {och: (True if och != 'none' else False) for och in on_chain_heuristics_list}
funding_address_entity, settlement_address_entity, = set_mapping(
    funding_address_entity,
    settlement_address_entity,
    on_chain_heuristics)

e_noccur = dict()  # entity and n occur in settlement txs
for tx in settlement_txs.values():
    for out in tx['outputs']:
        a = out['address']
        e = settlement_address_entity[a]
        if e not in e_noccur:
            e_noccur[e] = 0
        e_noccur[e] += 1

e_noccur_list = []
for e, n in e_noccur.items():
    e_noccur_list.append([e, n])

e_noccur_list.sort(key=lambda x: -x[1])
n_nodes_to_deanon = 40
i = 0
nodes_to_deanon = dict()
nodes_to_deanon['most_settlements'] = []
# nodes_to_deanon['snakes_collectors'] = []
nodes_to_deanon['random'] = []

for el in e_noccur_list:
    if i < n_nodes_to_deanon:
        entity, occur = el
        if entity in entity_node:
            nodes = entity_node[entity]
            for node in nodes:
                if node not in inactive_nodes and \
                        node not in [el[0] for el in nodes_to_deanon['most_settlements']]:
                    nodes_to_deanon['most_settlements'].append([node, entity])
                        # print(entity, node, occur)
                    i += 1

n_stars = 33
for entity, nodes in entity_node.items():
    for node in nodes:
        # if entity < - n_stars and \
        #         node not in nodes_to_deanon['most_settlements'] and\
        #         len(nodes_to_deanon['snakes_collectors']) < n_nodes_to_deanon:
            # nodes_to_deanon['snakes_collectors'].append([node, entity])
        if entity > 0 and \
                node not in [el[0] for el in nodes_to_deanon['most_settlements']] and \
                node not in [el[0] for el in nodes_to_deanon['random']] and \
                len(nodes_to_deanon['random']) < n_nodes_to_deanon and \
                node not in inactive_nodes:
            nodes_to_deanon['random'].append([node, entity])

write_json(nodes_to_deanon, output_file_1)

