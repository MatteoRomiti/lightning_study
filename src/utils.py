import json
import requests
from api_calls import get_address_entityID

level1_folder = '../data/joined/level_1/'
level2_folder = '../data/joined/level_2/'
results_folder = '../data/joined/results/'

on_chain_heuristics_list = ['none', 'stars', 'snakes', 'collectors', 'proxies', 'all']


def read_json(path, int_key=False, double_int_key=False):
    with open(path, 'r') as fp:
        js = json.load(fp)
    if int_key:
        return {int(k): v for k, v in js.items()}
    if double_int_key:
        return {int(conf): {int(e): ns for e, ns in mapping.items()} for conf, mapping in js.items()}
    return js


def write_json(js, path, int_key=False, values_to_list=False):
    if int_key:
        js = {int(k): v for k, v in js.items()}
    if values_to_list:
        js = {k: list(v) for k, v in js.items()}
    with open(path, 'w') as fp:
        json.dump(js, fp)


def fill_address_entity(address_entity):
    # fails = 1
    # while fails:
    print('Number of addresses', len(address_entity))
    fails = 0
    for i, a in enumerate(address_entity):
        if not isinstance(address_entity[a], int):
            try:
                print('address', i, end='\r')
                address_entity[a] = get_address_entityID(a)
            except Exception as e:
                fails += 1
                print('arrived at', i)
                print(e)
                return address_entity, fails
    return address_entity, fails


def get_blockstream_tx(hsh):
    bs_url = 'https://blockstream.info/api/tx/' + hsh
    r = requests.get(bs_url)
    d = json.loads(r.text)
    return d


def most_common(lst):
    return max(set(lst), key=lst.count)


def add_node_to_entity(entity, node, entity_nodes, found):
    # assign the other node to the other entity
    if entity not in entity_nodes:
        entity_nodes[entity] = set()
    if node not in entity_nodes[entity]:
        entity_nodes[entity].add(node)
        found = True
    return entity_nodes, found


def link_other_nodes(initial_entity_node, channels,
                     funded_address_settlement_txs, funding_txs,
                     settlement_address_entity):
    entity_node = {k: v for k, v in initial_entity_node.items()}
    found = True  # at least one new link
    i = 0
    while found:
        i += 1
        found = False  # until we find a new link
        print('Iteration:', i, '-- Number of linked entities:', len(entity_node))
        for channel in channels.values:
            funding_tx, out_index = channel[0].split(':')
            node_1 = channel[1]
            node_2 = channel[2]
            funded_address = \
                funding_txs[funding_tx]['vout'][int(out_index)]['scriptpubkey_address']

            settlement_txs = funded_address_settlement_txs[funded_address]
            # if channel is closed and number of outputs == 2 and
            # one node is mapped to one entity in the outputs
            if settlement_txs:  # it is always only one
                for settlement_tx in settlement_txs:
                    entities = list(
                        set([settlement_address_entity[out['scriptpubkey_address']]
                             for out in settlement_tx['vout']]))
                    if len(entities) == 2:
                        entity_1 = entities[0]
                        entity_2 = entities[1]
                        # if entity_1 is linked to one node in the channel,
                        # link the other node to the other entity
                        if entity_1 in entity_node:
                            # entity_1 has a node, find if it's in this channel
                            if node_1 in entity_node[entity_1]:
                                entity_node, found = \
                                    add_node_to_entity(entity_2,
                                                       node_2,
                                                       entity_node,
                                                       found)

                            elif node_2 in entity_node[entity_1]:
                                entity_node, found = \
                                    add_node_to_entity(entity_2,
                                                       node_1,
                                                       entity_node,
                                                       found)

                        # if entity_2 is linked to one node in the channel,
                        # link the other node to the other entity
                        if entity_2 in entity_node:
                            if node_1 in entity_node[entity_2]:
                                entity_node, found = \
                                    add_node_to_entity(entity_1,
                                                       node_2,
                                                       entity_node,
                                                       found)

                            elif node_2 in entity_node[entity_2]:
                                entity_node, found = \
                                    add_node_to_entity(entity_1,
                                                       node_1,
                                                       entity_node,
                                                       found)
    return entity_node


def invert_mapping(entity_node):
    node_entity = dict()
    for e, ns in entity_node.items():
        for n in ns:
            if n not in node_entity:
                node_entity[n] = set()
            node_entity[n].add(e)
    return node_entity


def get_results(r, entity_node, node_entity, conf=None):
    perc_entities_linked = round(100 * len(entity_node) / r['n_entities'], 2)
    perc_nodes_linked = round(100 * len(node_entity) / r['n_nodes'], 2)
    d = dict()
    d['n_entities_linked'] = len(entity_node)
    d['n_nodes_linked'] = len(node_entity)
    d['perc_entities_linked'] = perc_entities_linked
    d['perc_nodes_linked'] = perc_nodes_linked
    if conf:
        r[conf] = dict()
        for k, v in d.items():
            r[conf][k] = v
        return r
    for k, v in d.items():
        r[k] = v

    return r


def get_blockchain_page(tx_hash):
    url = 'https://www.blockchain.com/btc/tx/' + tx_hash
    r = requests.get(url)
    return r.text


def get_outputs_spenders(tx_hash, hash_page):
    spenders = []
    for i in [1, 2]:
        # spender = hash_page[tx_hash].split('spender')[i].split("\"")[4]
        spender = hash_page[tx_hash].split('spender')[i].split("\"")[6]
        if len(spender) == 64:
            spenders.append(spender)
    return spenders
