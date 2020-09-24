# This script uses the best linking result to see how many Bitcoin addresses
# get an LN attribution tag

from utils import read_json, results_folder, level2_folder
from load_data import funding_address_entity, settlement_address_entity, df_to_dicts_set
from sort_mapping_entities import relaxed, entity_star, entity_snake, entity_proxy
import pandas as pd

input_file_0 = results_folder + 'alias_address_clusters.csv'

if relaxed:
    results_folder += 'relaxed_filtered_'
else:
    results_folder += 'filtered_'

input_file_1 = results_folder + 'all_heuristic_1_node_entity.json'
input_file_1 = results_folder + 'all_heuristic_2_node_entity_conf.json'
input_file_2 = level2_folder + 'ip_address.csv'
input_file_3 = level2_folder + 'node.csv'
# node_entity = read_json(input_file_1)
node_entity = read_json(input_file_1, int_key=True)[2]

print(input_file_1)

ip_addresses = pd.read_csv(input_file_2)
nodes = pd.read_csv(input_file_3)
alias_ip_cluster = pd.read_csv(input_file_0)

node_cluster, cluster_node = df_to_dicts_set(alias_ip_cluster, invert=True)
node_alias, alias_node = df_to_dicts_set(nodes)
node_ip, ip_node = df_to_dicts_set(ip_addresses)

n_a = len(set(node_entity.keys()).intersection(set(node_alias.keys())))
print('nNodesLinkedWithAlias', n_a)

n_ip = len(set(node_entity.keys()).intersection(set(node_ip.keys())))
print('nNodesLinkedWithIP', n_ip)

print('nNodesAliasIPCluster', len(node_cluster))
intersection = set(node_entity.keys()).intersection(set(alias_ip_cluster.pub_key.values))
n_c = len(intersection)
print('nNodesLinkedAliasIPCluster', n_c)

# count the number of nodes that are not linked to entities but are in an
# alias/ip-based cluster of nodes where at least one node has been linked
# to an entity

linkable_nodes = set()
for cluster, nodes in cluster_node.items():
    all_nodes_are_linked = False
    possible_linkable_nodes = set()
    for node in nodes:
        if node in node_entity:
            all_nodes_are_linked = True
        else:
            possible_linkable_nodes.add(node)
    if all_nodes_are_linked:
        linkable_nodes = linkable_nodes.union(possible_linkable_nodes)
print('nNodesAliasIPLinkable', len(linkable_nodes))

tagged_entities = set()  # actually this should be tagged_components
alias_tagged_entities = set()
ip_tagged_entities = set()
for node in node_alias:
    if node in node_entity:
        tagged_entities = tagged_entities.union(node_entity[node])
        alias_tagged_entities = alias_tagged_entities.union(node_entity[node])
for node in node_ip:
    if node in node_entity:
        tagged_entities = tagged_entities.union(node_entity[node])
        ip_tagged_entities = ip_tagged_entities.union(node_entity[node])
print('nEntitiesAliasIPTagged', len(tagged_entities))
print('nEntitiesAliasTagged', len(alias_tagged_entities))
print('nEntitiesIPTagged', len(ip_tagged_entities))


def compute_tagged_addresses(tagged_entities):
    tagged_addresses = set()
    for address_entity in [funding_address_entity, settlement_address_entity]:
        for address, entity in address_entity.items():
            component = 0
            for entity_component in [entity_star, entity_snake, entity_proxy]:
                if entity in entity_component:
                    component = entity_component[entity]
            if not component:
                component = - entity
            if - component in tagged_entities:
                tagged_addresses.add(address)
    return tagged_addresses


tagged_addresses = compute_tagged_addresses(tagged_entities)
alias_tagged_addresses = compute_tagged_addresses(alias_tagged_entities)
ip_tagged_addresses = compute_tagged_addresses(ip_tagged_entities)

print('nAddressesAliasIPTagged', len(tagged_addresses))
print('nAddressesAliasTagged', len(alias_tagged_addresses))
print('nAddressesIPTagged', len(ip_tagged_addresses))
