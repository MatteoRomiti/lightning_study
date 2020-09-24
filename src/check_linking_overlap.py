# This script checks how much overlap we have between the two linking
# heuristics

from utils import results_folder, read_json
from sort_mapping_entities import relaxed

if relaxed:
    results_folder += 'relaxed_filtered_'
else:
    results_folder += 'filtered_'

och = ['none', 'star', 'snake', 'collector', 'proxy', 'all']

heuristic_1_entity_node_dict = dict()
heuristic_2_entity_node_dict = dict()

for h in och:
    heuristic_1_entity_node_dict[h] = read_json(results_folder + h + '_heuristic_1_entity_node.json', True)

for h in och:
    heuristic_2_entity_node_dict[h] = read_json(results_folder + h + '_heuristic_2_entity_node_conf.json', double_int_key=True)[2]

for h in och:
    print('On-chain heuristic used:', h)
#     entities_heuristics_1_2 = set(heuristic_1_entity_node.keys()) \
#         .intersection(set(heuristic_2b_entity_node_conf[conf].keys()))
    entities_heuristics_1_2 = set(heuristic_1_entity_node_dict[h]).intersection(set(heuristic_2_entity_node_dict[h]))
    # to see if the two heuristics say the same
    same = 0
    intersect = 0
    for e in entities_heuristics_1_2:
        s1 = set(heuristic_1_entity_node_dict[h][e])
        s2 = set(heuristic_2_entity_node_dict[h][e])
        if s1 == s2:
            same += 1
            intersect += 1
        elif s1.intersection(s2):
            intersect += 1
    print(same, 'entities out of', len(entities_heuristics_1_2),
          'entities in common are linked to the same nodes')
    print(intersect, 'entities out of', len(entities_heuristics_1_2),
          'entities in common are linked to at least on same node')
