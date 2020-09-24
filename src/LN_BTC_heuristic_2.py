# This script links BTC entities to LN nodes
# with the funding-entity-reuse heuristic

from utils import read_json, write_json, results_folder, invert_mapping, \
    link_other_nodes, get_results, on_chain_heuristics_list
from load_data import channels, funding_txs, funding_address_entity, \
    settlement_address_entity, funded_address_settlement_txs, \
    node_channels, set_mapping
from sort_mapping_entities import relaxed
from collections import Counter

output_file_0 = results_folder + 'funding_entity_channels_nodes.json'

if relaxed:
    results_folder += 'relaxed_filtered_'
else:
    results_folder += 'filtered_'

output_file_1 = results_folder + 'all_heuristic_2_entity_node_conf.json'
output_file_2 = results_folder + 'all_heuristic_2_node_entity_conf.json'
output_file_3a = results_folder + 'heuristic_2_results.json'
output_file_4 = results_folder + 'star_heuristic_2_entity_node_conf.json'
output_file_5 = results_folder + 'star_heuristic_2_node_entity_conf.json'
output_file_6 = results_folder + 'none_heuristic_2_entity_node_conf.json'
output_file_7 = results_folder + 'none_heuristic_2_node_entity_conf.json'
output_file_8 = results_folder + 'collector_heuristic_2_entity_node_conf.json'
output_file_9 = results_folder + 'collector_heuristic_2_node_entity_conf.json'
output_file_8b = results_folder + 'proxy_heuristic_2_entity_node_conf.json'
output_file_9b = results_folder + 'proxy_heuristic_2_node_entity_conf.json'
output_file_10 = results_folder + 'snake_heuristic_2_entity_node_conf.json'
output_file_11 = results_folder + 'snake_heuristic_2_node_entity_conf.json'


def heuristic_2(fae, sae, och):
    global output_file_1, output_file_2

    min_conf = 2  # min confidence level for results
    range_min_conf = [2, 3]  # to apply the heuristic with different min confidences

    funding_address_entity = {k: v for k, v in fae.items()}
    settlement_address_entity = {k: v for k, v in sae.items()}
    r = dict()
    r['n_funding_entities'] = len(set(funding_address_entity.values()))
    r['n_settlement_entities'] = len(set(settlement_address_entity.values()))
    r['n_entities'] = len(set(settlement_address_entity.values()).union(set(funding_address_entity.values())))
    r['n_addresses'] = len(set(settlement_address_entity.keys()).union(set(funding_address_entity.keys())))
    r['n_nodes'] = len(node_channels)

    funding_address_entity, settlement_address_entity, = \
        set_mapping(funding_address_entity, settlement_address_entity, och)

    # print('Start heuristic 2...')
    # print('Step 1:')
    # Confidence levels
    funding_entity_possible_nodes = dict()
    for channel in channels.values:
        funding_tx, out_index = channel[0].split(':')
        funding_address = funding_txs[funding_tx]['vin'][0]['prevout']['scriptpubkey_address']
        funding_entity = funding_address_entity[funding_address]
        if funding_entity not in funding_entity_possible_nodes:
            funding_entity_possible_nodes[funding_entity] = []
        funding_entity_possible_nodes[funding_entity].append(channel[1])
        funding_entity_possible_nodes[funding_entity].append(channel[2])

    # each funding entity that has at least n_channels possible nodes
    # (confidence level >= n_channels)
    n_channels = min_conf
    entity_channels_half = []
    fe_confidence = []
    fe_confidence_dict = dict()
    for fe, pns in funding_entity_possible_nodes.items():
        if len(pns) >= n_channels * 2:  # *2 cause we have two nodes per channel
            pn_occur = Counter(pns)
            for pn, occur in pn_occur.items():
                if occur * 2 == len(pns):
                    fe_confidence.append([fe, occur])
                    fe_confidence_dict[fe] = occur
                    entity_channels_half.append(occur)
    entity_channels_half.sort()

    confidence_linked = dict()
    funding_entity_channels_nodes = dict()
    node_possible_entities = dict()
    # populate funding_entity_channels_nodes
    for channel in channels.values:
        funding_tx, out_index = channel[0].split(':')
        funding_address = funding_txs[funding_tx]['vin'][0]['prevout']['scriptpubkey_address']
        funding_entity = funding_address_entity[funding_address]
        if funding_entity not in funding_entity_channels_nodes:
            # use chan_point as key
            funding_entity_channels_nodes[funding_entity] = dict()
        # add nodes
        funding_entity_channels_nodes[funding_entity][channel[0]] = [channel[1],
                                                                     channel[2]]
        for i in [1, 2]:
            if channel[i] not in node_possible_entities:
                node_possible_entities[channel[i]] = set()
            node_possible_entities[channel[i]].add(funding_entity)

    write_json(funding_entity_channels_nodes, output_file_0)

    heuristic_2a_entity_node_conf = dict()
    for min_confidence_level in range(range_min_conf[0], range_min_conf[1]):
        # create link between entity and a node when
        # the node is the only one present in every channel of the entity
        heuristic_2a_entity_node_conf[min_confidence_level] = dict()  # linking
        for fe in funding_entity_channels_nodes:
            # count number of occurrences of each node in channels
            node_occur = dict()

            # compute node_occur
            for channel in funding_entity_channels_nodes[fe]:
                for node in funding_entity_channels_nodes[fe][channel]:
                    if node not in node_occur:
                        node_occur[node] = 0
                    node_occur[node] += 1

            # get max_occur
            max_occur = max(node_occur.values())
            selected_node = None

            # check if there is a perfect max_occur, i.e.,
            # if max_occur is unique and in every channel
            # (corresponding node is in every channel)
            if list(node_occur.values()).count(max_occur) == 1 \
                    and max_occur == len(funding_entity_channels_nodes[fe]) \
                    and max_occur >= min_confidence_level:
                # get node present in every channel and add it to its entity
                selected_node = [n for n, occ in node_occur.items()
                                 if occ == max_occur][0]
                if fe not in heuristic_2a_entity_node_conf[min_confidence_level]:
                    heuristic_2a_entity_node_conf[min_confidence_level][fe] = set()
                heuristic_2a_entity_node_conf[min_confidence_level][fe] \
                    .add(selected_node)
        confidence_linked[min_confidence_level] = \
            len(heuristic_2a_entity_node_conf[min_confidence_level])

    # print('Step 2:')
    heuristic_2b_entity_node_conf = dict()
    for conf in heuristic_2a_entity_node_conf:
        # print()
        # print('=' * 5, 'Confidence level:', conf, '=' * 5)
        heuristic_2b_entity_node_conf[conf] = \
            link_other_nodes(heuristic_2a_entity_node_conf[conf], channels,
                             funded_address_settlement_txs, funding_txs,
                             settlement_address_entity)

    heuristic_2b_node_entity_conf = dict()
    for conf in heuristic_2b_entity_node_conf:
        heuristic_2b_node_entity_conf[conf] = \
            invert_mapping(heuristic_2b_entity_node_conf[conf])

    for conf in range(range_min_conf[0], range_min_conf[1]):
        r = get_results(r, heuristic_2b_entity_node_conf[conf],
                        heuristic_2b_node_entity_conf[conf], conf)

        addresses_linked = set()
        for address_entity in [funding_address_entity, settlement_address_entity]:
            for address, entity in address_entity.items():
                if entity in heuristic_2b_entity_node_conf[conf]:
                    addresses_linked.add(address)
        r['perc_addresses_linked'] = round(
            100*len(addresses_linked)/r['n_addresses'], 2)

    output_file_a = output_file_1
    output_file_b = output_file_2
    if och['stars']:
        output_file_a = output_file_4
        output_file_b = output_file_5
    if och['none']:
        output_file_a = output_file_6
        output_file_b = output_file_7
    if och['snakes']:
        output_file_a = output_file_10
        output_file_b = output_file_11
    if och['collectors']:
        output_file_a = output_file_8
        output_file_b = output_file_9
    if och['proxies']:
        output_file_a = output_file_8b
        output_file_b = output_file_9b
    if och['all']:
        output_file_a = output_file_1
        output_file_b = output_file_2

    # Write to file
    heuristic_2_entity_node_conf = \
        {conf: {str(k): [e for e in v] for k, v in
                heuristic_2b_entity_node_conf[conf].items()} for conf in
         heuristic_2b_entity_node_conf}
    heuristic_2_node_entity_conf = \
        {conf: {k: [int(e) for e in v] for k, v in
                heuristic_2b_node_entity_conf[conf].items()} for conf in
         heuristic_2b_node_entity_conf}
    print(och)
    print('writing to', output_file_a, output_file_b)
    write_json(heuristic_2_entity_node_conf, output_file_a)
    write_json(heuristic_2_node_entity_conf, output_file_b)

    return r


on_chain_heuristics = {och: False for och in on_chain_heuristics_list}

results = dict()
for och in on_chain_heuristics:
    if och != 'all':
        on_chain_heuristics[och] = True
        results[och] = heuristic_2(funding_address_entity, settlement_address_entity, on_chain_heuristics)
        on_chain_heuristics[och] = False

on_chain_heuristics = {och: (True if och != 'none' else False) for och in on_chain_heuristics_list}
results['all'] = heuristic_2(funding_address_entity, settlement_address_entity, on_chain_heuristics)
write_json(results, output_file_3a)


