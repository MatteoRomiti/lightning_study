# This script prints how many questionable links are created
# by heuristic 2 based on nodes' on-chain activity time overlap

from utils import read_json, results_folder
from load_data import node_openings_closings
import itertools

input_file1 = results_folder + 'filtered_all_heuristic_2_entity_node_conf.json'
input_file2 = results_folder + 'filtered_all_heuristic_2_node_entity_conf.json'
input_file3 = results_folder + 'funding_entity_channels_nodes.json'

heuristic_2_entity_node_conf = read_json(input_file1, double_int_key=True)

funding_entity_channels_nodes = read_json(input_file3, True)

conf = 2
entity_nodes_to_plot = dict()
# for each entity-node pair:
for entity, nodes in heuristic_2_entity_node_conf[conf].items():
    # if it is a funding entity
    if entity in funding_entity_channels_nodes:
        entity_nodes_to_plot[entity] = set()
        # plot time overlap of other nodes in channels
        for channel in funding_entity_channels_nodes[entity]:
            for other_node in funding_entity_channels_nodes[entity][channel]:
                if other_node not in nodes:
                    # add it to list to check
                    entity_nodes_to_plot[entity].add(other_node)
                # else is linked to entity
    # else, we should check what happens here

i = 0
entities_without_overlap = set()
for e, ns in entity_nodes_to_plot.items():
    if len(ns) > 1:
        overlap = False
        # find if there is at least one time overlap among other-nodes
        combs = list(itertools.combinations(ns, 2))
        # for each possible pair
        for comb in combs:
            n1, n2 = comb
            # if the max of one is greater than the min of the other
            # or the max of the other is greater than the min of one
            if node_openings_closings[n1]['last_activity'] > node_openings_closings[n2]['first_activity'] or node_openings_closings[n2]['last_activity'] > node_openings_closings[n1]['first_activity']:
                # we have overlap
                overlap = True
                break
        if not overlap:
            entities_without_overlap.add(e)
#         print(e)
#         plot_nodes_time_overlap(ns)
print('Number of questionable attributions:', len(entities_without_overlap))
