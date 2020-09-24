# This script links BTC entities to LN nodes
# with the coin-reuse-entity heuristic

from utils import read_json, write_json, level1_folder, results_folder, \
    most_common, link_other_nodes, invert_mapping, get_results, \
    on_chain_heuristics_list
from load_data import channels, funding_txs, settlement_addresses,\
    funded_address_settlement_txs, settlement_txs_hashes, set_mapping, \
    funding_address_entity, settlement_address_entity, node_channels, \
    node_openings_closings
from sort_mapping_entities import relaxed

input_file1 = level1_folder + 'chpoints_reusing_coins.json'
settlement_addresses = set(settlement_addresses)

if relaxed:
    results_folder += 'relaxed_filtered_'
else:
    results_folder += 'filtered_'

output_file_1 = results_folder + 'all_heuristic_1_entity_node.json'
output_file_2 = results_folder + 'all_heuristic_1_node_entity.json'
output_file_3 = results_folder + 'heuristic_1_results.json'
output_file_3b = results_folder + 'heuristic_1_results_no_later_stars.json'
output_file_4 = results_folder + 'star_heuristic_1_entity_node.json'
output_file_5 = results_folder + 'star_heuristic_1_node_entity.json'
output_file_6 = results_folder + 'none_heuristic_1_entity_node.json'
output_file_7 = results_folder + 'none_heuristic_1_node_entity.json'
output_file_8 = results_folder + 'collector_heuristic_1_entity_node.json'
output_file_9 = results_folder + 'collector_heuristic_1_node_entity.json'
output_file_10 = results_folder + 'proxy_heuristic_1_entity_node.json'
output_file_11 = results_folder + 'proxy_heuristic_1_node_entity.json'
output_file_12 = results_folder + 'snake_heuristic_1_entity_node.json'
output_file_13 = results_folder + 'snake_heuristic_1_node_entity.json'

use_entities = True


def heuristic_1(fae, sae, och):
    global output_file_1, output_file_2

    funding_address_entity = {k: v for k, v in fae.items()}
    settlement_address_entity = {k: v for k, v in sae.items()}
    r = dict()
    r['n_funding_entities'] = len(set(funding_address_entity.values()))
    r['n_settlement_entities'] = len(set(settlement_address_entity.values()))
    r['n_entities'] = len(set(settlement_address_entity.values()).union(set(funding_address_entity.values())))
    r['n_addresses'] = len(set(settlement_address_entity.keys()).union(set(funding_address_entity.keys())))
    r['n_nodes'] = len(node_channels)

    funding_address_entity, settlement_address_entity = \
        set_mapping(funding_address_entity, settlement_address_entity, och)

    # print('Start heuristic 1...')
    chpoints_reusing_coins = read_json(input_file1)

    # print('use_entities', use_entities)

    # # mapping between stx and its ftx
    stx_its_chpoint = dict()
    for channel in channels.values:
        funding_tx, out_index = channel[0].split(':')
        funded_address = funding_txs[funding_tx]['vout'][int(out_index)]['scriptpubkey_address']
        settlement_txs = funded_address_settlement_txs[funded_address]
        if len(settlement_txs) == 1:  # it is always zero or one tx
            stx = settlement_txs[0]['txid']
            if stx not in stx_its_chpoint:
                stx_its_chpoint[stx] = channel[0]
            else:
                print('stx already in dict', stx)

    # create links for heuristic 1 (both at address and entity level)
    stx_a_chpoint = []  # list of settlement tx, address, funding tx
    for chpoint in chpoints_reusing_coins:
        hsh, out_index = chpoint.split(':')
        uftx = funding_txs[hsh]
        for i in uftx['vin']:
            a = i['prevout']['scriptpubkey_address']
            prev_tx = i['txid']
            if a in settlement_addresses:
                if prev_tx in settlement_txs_hashes:
                    stx_a_chpoint.append([prev_tx, a, chpoint])
    #             else:
    #                 # a is a settlement_address but prev_tx is not a
    #                 settlement_tx in our data

    stx_e_chpoint = []  # list of settlement tx, entity, funding tx
    for chpoint in chpoints_reusing_coins:
        hsh, out_index = chpoint.split(':')
        uftx = funding_txs[hsh]
        for i in uftx['vin']:
            e = funding_address_entity[i['prevout']['scriptpubkey_address']]
            prev_tx = i['txid']
            if e in settlement_address_entity.values():
                if prev_tx in settlement_txs_hashes:
                    stx_e_chpoint.append([prev_tx, e, chpoint])

    # I need a mapping between ch_point and nodes
    # and between settlement tx and nodes
    chpoint_nodes = dict()
    for channel in channels.values:
        chpoint_nodes[channel[0]] = [channel[1], channel[2]]

    funded_address_chpoint = dict()
    for chpoint in channels.chan_point.values:
        hsh, out_index = chpoint.split(':')
        funded_address = funding_txs[hsh]['vout'][int(out_index)]['scriptpubkey_address']
        if funded_address not in funded_address_chpoint:
            funded_address_chpoint[funded_address] = chpoint
        else:
            print(funded_address, ' has multiple channels')

    stx_nodes = dict()
    for fa, chpoint in funded_address_chpoint.items():
        stxs = funded_address_settlement_txs[fa]
        if stxs:
            stx = stxs[0]['txid']
            stx_nodes[stx] = chpoint_nodes[chpoint]

    # print('Initial number of links addresses', len(stx_a_ftx))
    # print('Initial number of links entities', len(stx_e_ftx))

    # decide link level
    triplet = stx_a_chpoint
    if use_entities:
        triplet = stx_e_chpoint

    links = []  # like stx_a_chpoint plus 4 nodes of channels
    for el in triplet:
        # the funding entity controls the node in common between the channel
        # opened with ftx and closed with stx
        stx, a, chpoint = el
        n1, n2 = chpoint_nodes[chpoint]  # happens after the stx
        n3, n4 = stx_nodes[stx]
        links.append([stx, a, chpoint, n1, n2, n3, n4])

    useful_links = []
    for link in links:
        s = set(link[3:])
        if len(s) == 3:
            useful_links.append(link)

    # if closing of other node in ch1 > opening of other node in ch2
    # then we can use the link
    usable_links = []
    for link in useful_links:
        node_in_common = most_common(link[3:])
        other_node_ch1 = ''
        other_node_ch2 = ''
        for node in link[3:][::-1]:
            if node != node_in_common:
                if not other_node_ch1:
                    other_node_ch1 = node
                else:
                    other_node_ch2 = node
        if node_openings_closings[other_node_ch1]['last_activity'] > \
                node_openings_closings[other_node_ch2]['first_activity']:
            usable_links.append(link)

    reliable_links_addresses = []
    for link in usable_links:
        link_address = link[1]
        stx = link[0]
        its_ftx = stx_its_chpoint[stx].split(':')[0]
        if link_address in [el['prevout']['scriptpubkey_address'] for el in
                            funding_txs[its_ftx]['vin']]:
            reliable_links_addresses.append(link)
    print('Number of reliable links at address level:',
          len(reliable_links_addresses))

    reliable_links_entities = []
    entities_reusing = set()
    for link in usable_links:
        if use_entities:
            link_entity = link[1]
        else:
            link_entity = settlement_address_entity[link[1]]
        stx = link[0]
        its_ftx = stx_its_chpoint[stx].split(':')[0]
        if link_entity in [funding_address_entity[el['prevout']['scriptpubkey_address']] for el
                           in funding_txs[its_ftx]['vin']]:
            entities_reusing.add(link_entity)
            reliable_links_entities.append(link)

    print('Number of reliable links at entity level:', len(reliable_links_entities))
    print('Number of entities reusing funding addresses:', len(entities_reusing))

    # step 1: linking nodes to entity using stx and ftx
    # print('Step 1:')
    heuristic_1a_entity_node = dict()
    heuristic_1a_node_entity = dict()
    for link in reliable_links_entities:
        if use_entities:
            e = link[1]
        else:
            e = settlement_address_entity[link[1]]
        n = most_common(link[3:])
        if e not in heuristic_1a_entity_node:
            heuristic_1a_entity_node[e] = set()
        heuristic_1a_entity_node[e].add(n)
        if n not in heuristic_1a_node_entity:
            heuristic_1a_node_entity[n] = set()
        heuristic_1a_node_entity[n].add(e)
    # print('Number of entities linked to nodes:', len(heuristic_1a_entity_node))
    # print('Number of nodes linked to entities:', len(heuristic_1a_node_entity))

    # print('Step 2:')
    # link other node and entity in channel
    heuristic_1b_entity_node = link_other_nodes(heuristic_1a_entity_node, channels,
                                                funded_address_settlement_txs,
                                                funding_txs,
                                                settlement_address_entity)
    heuristic_1b_node_entity = invert_mapping(heuristic_1b_entity_node)

    # correct means that the settlement tx has exactly two output entities
    correct_stxs = []  # correct stxs
    correct_settlement_entities = set()  # output entities of correct stxs
    correct_nodes = set()
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
                # count entities
                entities = set([settlement_address_entity[out['scriptpubkey_address']]
                                for out in settlement_tx['vout']])
                if len(entities) == 2:
                    correct_stxs.append(settlement_tx)
                    correct_settlement_entities = correct_settlement_entities.union(entities)
                    correct_nodes.add(node_1)
                    correct_nodes.add(node_2)

    perc_entities_linked_settled = round(100 * len(heuristic_1b_entity_node) / r['n_settlement_entities'], 2)
    perc_entities_linked_2e = round(100 * len(heuristic_1b_entity_node) / len(correct_settlement_entities), 2)
    perc_nodes_linked_2e = round(100 * len(heuristic_1b_node_entity) / len(correct_nodes), 2)

    r = get_results(r, heuristic_1b_entity_node, heuristic_1b_node_entity)

    print('Number of settlement entities:', r['n_settlement_entities'], '--', perc_entities_linked_settled, '% linked')
    print('Number of settlement entities considering settlement txs with 2 output entities:', len(correct_settlement_entities), '--', perc_entities_linked_2e, '% linked')
    print('Number of nodes considering settlement txs with 2 output entities:', len(correct_nodes), '--', perc_nodes_linked_2e, '% linked')

    addresses_linked = set()
    for address_entity in [funding_address_entity, settlement_address_entity]:
        for address, entity in address_entity.items():
            if entity in heuristic_1b_entity_node:
                addresses_linked.add(address)
    r['perc_addresses_linked'] = round(
        100 * len(addresses_linked) / r['n_addresses'], 2)

    output_file_a = output_file_1
    output_file_b = output_file_2
    if och['stars']:
        output_file_a = output_file_4
        output_file_b = output_file_5
    if och['none']:
        output_file_a = output_file_6
        output_file_b = output_file_7
    if och['snakes']:
        output_file_a = output_file_12
        output_file_b = output_file_13
    if och['collectors']:
        output_file_a = output_file_8
        output_file_b = output_file_9
    if och['proxies']:
        output_file_a = output_file_10
        output_file_b = output_file_11
    if och['all']:
        output_file_a = output_file_1
        output_file_b = output_file_2

    # Write to file
    heuristic_1_entity_node = {str(k): [e for e in v]
                               for k, v in heuristic_1b_entity_node.items()}
    heuristic_1_node_entity = {k: [int(e) for e in v]
                               for k, v in heuristic_1b_node_entity.items()}
    print(och)
    print('writing to', output_file_a, output_file_b)
    write_json(heuristic_1_entity_node, output_file_a)
    write_json(heuristic_1_node_entity, output_file_b)

    return r


on_chain_heuristics = {och: False for och in on_chain_heuristics_list}

results = dict()
for och in on_chain_heuristics:
    # one by one
    if och != 'all':
        on_chain_heuristics[och] = True
        results[och] = heuristic_1(funding_address_entity, settlement_address_entity, on_chain_heuristics)
        on_chain_heuristics[och] = False

# all
on_chain_heuristics = {och: (True if och != 'none' else False) for och in on_chain_heuristics_list}
results['all'] = heuristic_1(funding_address_entity, settlement_address_entity, on_chain_heuristics)
write_json(results, output_file_3)
