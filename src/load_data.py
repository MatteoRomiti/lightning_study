# This script loads data to be imported from other scripts

import pandas as pd
import time
from utils import read_json, level1_folder, level2_folder, results_folder
from sort_mapping_entities import star_file, snake_file, collector_file, proxy_file

input_file_1 = level2_folder + 'channel.csv'
input_file_2 = level2_folder + 'node.csv'
input_file_3 = level2_folder + 'ip_address.csv'
input_file_4 = level1_folder + 'blockstream_funding_txs.json'
input_file_5 = level1_folder + 'funding_address_entity.json'
input_file_6 = level1_folder + 'funded_address_blockstream_settlement_txs.json'
input_file_7 = level1_folder + 'settlement_address_entity.json'
input_file_8 = level1_folder + 'settlement_addresses.json'
input_file_9 = level1_folder + 'blockstream_settlement_txs.json'
input_file_10 = star_file
input_file_11 = snake_file
input_file_12 = collector_file
input_file_12b = proxy_file
input_file_13 = results_folder + 'star_sorted_mapping.json'
input_file_14 = results_folder + 'snake_sorted_mapping.json'
input_file_15 = results_folder + 'collector_sorted_mapping.json'
input_file_15b = results_folder + 'proxy_sorted_mapping.json'


def df_to_dicts_set(df, invert=False):
    node_x = dict()
    x_node = dict()
    for el in df.values:
        el0 = el[0]
        el1 = el[1]
        if invert:
            el0 = el[1]
            el1 = el[0]
        if el0 not in node_x:
            node_x[el0] = set()
        node_x[el0].add(el1)
        if el1 not in x_node:
            x_node[el1] = set()
        x_node[el1].add(el0)
    return node_x, x_node


def create_mapping(components_df, component_sorted_mapping):
    component_entities = dict()
    for e in components_df.values:
        component = int(e[0])
        entity = int(e[1])
        sorted_id = int(component_sorted_mapping[component])
        if sorted_id not in component_entities:
            component_entities[sorted_id] = []
        component_entities[sorted_id].append(entity)
    return component_entities


def invert_mapping_component(component_entities):
    entity_component = dict()
    for component, entities in component_entities.items():
        for e in entities:
            entity_component[e] = component
    return entity_component


def replace_ids(mapping_dict, address_entity):
    for address, entity in address_entity.items():
        if entity in mapping_dict:
            # use negative values to avoid collision with standard IDs
            address_entity[address] = - mapping_dict[entity]
    return address_entity


def mapping(csv_file, json_file, fae, sae):
    # modify address-entity mapping: entities->components (negative IDs)
    components_df = pd.read_csv(csv_file)
    component_sorted_mapping = read_json(json_file, True)

    # mapping
    component_entities = create_mapping(components_df, component_sorted_mapping)
    entity_component = invert_mapping_component(component_entities)

    fae = replace_ids(entity_component, fae)
    sae = replace_ids(entity_component, sae)

    return fae, sae


def use_stars(fae, sae):
    print('use_stars')
    return mapping(input_file_10, input_file_13, fae, sae)


def use_snakes(fae, sae):
    print('use_snakes')
    return mapping(input_file_11, input_file_14, fae, sae)


def use_collectors(fae, sae):
    print('use_collectors')
    return mapping(input_file_12, input_file_15, fae, sae)


def use_proxies(fae, sae):
    print('use_proxies')
    return mapping(input_file_12b, input_file_15b, fae, sae)


def set_mapping(fae, sae, och):
    if och['stars']:
        fae, sae = use_stars(fae, sae)
    if och['snakes']:
        fae, sae = use_snakes(fae, sae)
    if och['collectors']:
        fae, sae = use_collectors(fae, sae)
    if och['proxies']:
        fae, sae = use_proxies(fae, sae)
    return fae, sae


############### LN Data ###############
channels = pd.read_csv(input_file_1)
nodes = pd.read_csv(input_file_2)
ip_addresses = pd.read_csv(input_file_3)

node_channels = dict()
for channel in channels.values:
    c, n1, n2 = channel
    if n1 not in node_channels:
        node_channels[n1] = set()
    node_channels[n1].add(c)
    if n2 not in node_channels:
        node_channels[n2] = set()
    node_channels[n2].add(c)

node_alias, alias_node = df_to_dicts_set(nodes)
node_ip, ip_node = df_to_dicts_set(ip_addresses)


############### BTC Data ###############
funding_txs = read_json(input_file_4)
funding_address_entity = read_json(input_file_5)
funded_address_settlement_txs = read_json(input_file_6)
settlement_address_entity = read_json(input_file_7)
settlement_addresses = read_json(input_file_8)
settlement_txs = read_json(input_file_9)
settlement_txs_hashes = list(settlement_txs.keys())

# Nodes on-chain activity
# for each node, create a list of timestamps of
# openings, closings and first/last_activity
node_openings_closings = dict()
for node, chnls in node_channels.items():
    node_openings_closings[node] = {'openings': [], 'closings': []}
    for chnl in chnls:
        tx_hsh, out_index = chnl.split(':')
        t_open = funding_txs[tx_hsh]['status']['block_time']
        node_openings_closings[node]['openings'].append(t_open)

        t_closed = 0
        funded_address = funding_txs[tx_hsh]['vout'][int(out_index)]['scriptpubkey_address']
        stxs = funded_address_settlement_txs[funded_address]
        if stxs:
            t_closed = stxs[0]['status']['block_time']
        node_openings_closings[node]['closings'].append(t_closed)
    node_openings_closings[node]['first_activity'] = min(
        node_openings_closings[node]['openings'])
    node_openings_closings[node]['last_activity'] = max(
        max(node_openings_closings[node]['openings']),
        max(node_openings_closings[node]['closings']))
    if min(node_openings_closings[node]['closings']) == 0:
        # still open -> now
        node_openings_closings[node]['last_activity'] = int(time.time())
