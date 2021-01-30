import json
import numpy as np
import requests
import scipy.cluster.hierarchy
import pylcs  # longest common subsequence
from jellyfish import jaro_winkler_similarity, hamming_distance, \
    damerau_levenshtein_distance, jaro_similarity

from ipaddress import IPv4Address, IPv4Network, IPv6Address, IPv6Network
import pandas as pd

from api_calls import get_address_entityID, api_path, url2dict

level1_folder = '../../data/level_1/'
level2_folder = '../../data/level_2/'
results_folder = '../../data/results/'

address_categories_csv_file = level1_folder + 'address_categories.csv'
alias_address_clusters_csv_file = results_folder + 'alias_address_clusters.csv'
entity_nbrs_file = level1_folder + 'entity_nbrs.json'
gt_address_txs_file = level1_folder + 'gt_address_txs.json'
channels_file = level2_folder + 'channel.csv'
funding_txs_file = level1_folder + 'funding_txs.json'
funding_addresses_file = level1_folder + 'funding_addresses.json'
funding_addresses_csv_file = level1_folder + 'funding_addresses.csv'
funding_address_entity_file = level1_folder + 'funding_address_entity.json'
funding_entity_channels_nodes_file = results_folder + 'funding_entity_channels_nodes.json'
funding_node_channel_csv_file = results_folder + 'funding_node_channel.csv'
funded_address_settlement_txs_file = level1_folder + 'funded_address_settlement_txs.json'
nodes_csv_file = level2_folder + 'node.csv'
ips_csv_file = level2_folder + 'ip_address.csv'
whois_csv_file = level2_folder + 'whois.csv'
snapshot_csv_file = level2_folder + 'lnsnapshot2020-09-09.csv'
outgoing_channels_file = results_folder + 'closedchannels.json'
gt_node_entity_file = results_folder + 'gt_node_entity.json'
incoming_channels_file = level2_folder + 'inbound_channels.csv'
settlement_txs_file = level1_folder + 'settlement_txs.json'
samourai_txs_file = level1_folder + 'samourai_txs.json'
settlement_addresses_file = level1_folder + 'settlement_addresses.json'
settlement_addresses_csv_file = level1_folder + 'settlement_addresses.csv'
settlement_address_entity_file = level1_folder + 'settlement_address_entity.json'
settlement_txs_with_punishment_file = results_folder + 'settlement_txs_with_punishment.json'
spender_details_file = level1_folder + 'spender_details.json'
unilateral_settlement_txs_with_p2wsh_in_outputs_spenders_file = level1_folder + 'unilateral_settlement_txs_with_p2wsh_in_outputs_spenders.json'
inactive_nodes_file = level2_folder + 'inactive_selected_nodes.json'
target_nodes_file = results_folder + 'target_nodes.json'


patterns_files = dict()
patterns_files['stars'] = results_folder + 'funding_cluster_star_pattern_filtered.csv'
patterns_files['snakes'] = results_folder + 'funding_cluster_snake_pattern_filtered.csv'
patterns_files['collectors'] = results_folder + 'settlement_cluster_collector_pattern_filtered.csv'
patterns_files['proxies'] = results_folder + 'settlement_cluster_collector_pattern_extended_filtered.csv'

patterns_sorted_files = dict()
patterns_sorted_files['stars'] = results_folder + 'star_sorted_mapping.json'
patterns_sorted_files['snakes'] = results_folder + 'snake_sorted_mapping.json'
patterns_sorted_files['collectors'] = results_folder + 'collector_sorted_mapping.json'
patterns_sorted_files['proxies'] = results_folder + 'proxy_sorted_mapping.json'

chpoints_reusing_coins_file = level1_folder + 'chpoints_reusing_coins.json'

last_block = 647529
on_chain_heuristics_list = ['none', 'stars', 'snakes', 'collectors', 'proxies', 'all']
patterns_list = [el for el in on_chain_heuristics_list if el not in ['none', 'all']]
wasabi_addresses = {'bc1qs604c7jv6amk4cxqlnvuxv26hv3e48cds4m0ew', 'bc1qa24tsgchvuxsaccp8vrnkfd85hrcpafg20kmjw'}

heuristics_files = dict()
for n in [1, 2]:
    heuristics_files[n] = dict()
    for och in on_chain_heuristics_list:
        heuristics_files[n][och] = results_folder + och + '_' + str(n) + '_entity_node.json', results_folder + och + '_' + str(n) + '_node_entity.json'
    heuristics_files[n]['results'] = results_folder + str(n) + '_linking_results.json'


def read_json(path, int_key=False, double_int_key=False, values_to_set=False):
    with open(path, 'r') as fp:
        js = json.load(fp)
    if values_to_set:
        js = {k: set(v) for k, v in js.items()}
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


def set_mapping(fae_, sae_, och):

    fae = {k: v for k, v in fae_.items()}
    sae = {k: v for k, v in sae_.items()}

    for p in patterns_list:
        if och[p]:
            print('use', p)
            fae, sae = mapping(patterns_files[p],
                               patterns_sorted_files[p], fae, sae)
    return fae, sae


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


def get_not_available_txs(hsh_tx):
    not_available_txs = set()
    for hsh, tx in hsh_tx.items():
        block = tx['status']['block_height']
        if block > last_block:
            not_available_txs.add(hsh)
    return not_available_txs


def get_available_txs(hsh_tx):
    not_available_txs = get_not_available_txs(hsh_tx)
    available_hsh_tx = dict()
    for hsh, tx in hsh_tx.items():
        if hsh not in not_available_txs:
            available_hsh_tx[hsh] = tx
    return available_hsh_tx


def df_to_two_dicts(components_df):
    entity_component = dict()
    component_entities = dict()
    for e in components_df.values:
        cluster, entity = e
        if cluster not in component_entities:
            component_entities[cluster] = []
        component_entities[cluster].append(entity)
        entity_component[entity] = cluster
    return entity_component, component_entities


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


def add_node_to_entity(node, entity, entity_nodes):
    if entity not in entity_nodes:
        entity_nodes[entity] = set()
    entity_nodes[entity].add(node)
    return entity_nodes


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


def add_node_to_entity_found(entity, node, entity_nodes, found):
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
                                    add_node_to_entity_found(entity_2,
                                                       node_2,
                                                       entity_node,
                                                       found)

                            elif node_2 in entity_node[entity_1]:
                                entity_node, found = \
                                    add_node_to_entity_found(entity_2,
                                                       node_1,
                                                       entity_node,
                                                       found)

                        # if entity_2 is linked to one node in the channel,
                        # link the other node to the other entity
                        if entity_2 in entity_node:
                            if node_1 in entity_node[entity_2]:
                                entity_node, found = \
                                    add_node_to_entity_found(entity_1,
                                                       node_2,
                                                       entity_node,
                                                       found)

                            elif node_2 in entity_node[entity_2]:
                                entity_node, found = \
                                    add_node_to_entity_found(entity_1,
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


def get_results(r, entity_node, node_entity):
    perc_entities_linked = round(100 * len(entity_node) / r['n_entities'], 2)
    perc_nodes_linked = round(100 * len(node_entity) / r['n_nodes'], 2)
    d = dict()
    d['n_entities_linked'] = len(entity_node)
    d['n_nodes_linked'] = len(node_entity)
    d['perc_entities_linked'] = perc_entities_linked
    d['perc_nodes_linked'] = perc_nodes_linked
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


def get_entity_neighbors(entity, currency='btc'):
    nbrs_out = get_entity_neighbors_out(entity, currency)
    nbrs_in = get_entity_neighbors_in(entity, currency)
    return nbrs_in.union(nbrs_out)


def get_entity_neighbors_out(entity, currency='btc'):
    # get all entities receiving money from this entity
    neighbors_out = set()
    url = api_path + currency + '/' + 'entities/' + str(entity) + '/neighbors?direction=out'
    d = url2dict(url)
    if 'neighbors' in d:
        for n in d['neighbors']:
            neighbors_out.add(int(n['id']))
    return neighbors_out


def get_entity_neighbors_in(entity, currency='btc'):
    # get all entities sending money to this entity
    neighbors_in = set()
    url = api_path + currency + '/' + 'entities/' + str(entity) + '/neighbors?direction=in'
    d = url2dict(url)
    if 'neighbors' in d:
        for n in d['neighbors']:
            neighbors_in.add(int(n['id']))
    return neighbors_in


def is_reserved_address(ip_address):
    if ".onion" in ip_address:
        return False
    special_use_nets_ipv4 = ["0.0.0.0/8", "10.0.0.0/8", "100.64.0.0/10", "127.0.0.0/8", "169.254.0.0/16", "172.16.0.0/12", "192.0.0.0/24", "192.0.2.0/24",
                             "192.88.99.0/24", "192.168.0.0/16", "198.18.0.0/15", "198.51.100.0/24", "203.0.113.0/24", "224.0.0.0/4", "240.0.0.0/4", "255.255.255.255/32"]
    special_use_nets_ipv6 = ["::/0", "::/128", "::1/128", "::ffff:0:0/96", "::ffff:0:0:0/96", "64:ff9b::/96",
                             "100::/64", "2001::/32", "2001:20::/28", "2001:db8::/32", "2002::/16", "fc00::/7", "fe80::/10", "ff00::/8"]
    if ":" in ip_address:  # ipv6
        return any([IPv6Address(ip_address) in IPv6Network(net) for net in special_use_nets_ipv6])
    else:  # ipv4
        return any([IPv4Address(ip_address) in IPv4Network(net) for net in special_use_nets_ipv4])


def compute_distances(alias_df, distance_func):
    # https://codereview.stackexchange.com/questions/37026/string-matching-and-clustering
    # generate pairwise indices of the alias dataframe without duplication
    pairwise_indices = np.triu_indices(len(alias_df.alias), 1)

    def get_dist(coord):
        i, j = coord
        # compute distance with some distance metric
        return distance_func(alias_df.alias.iloc[i], alias_df.alias.iloc[j])

    # compute pairwise distances
    dists = np.apply_along_axis(get_dist, 0, pairwise_indices)

    return dists


def cluster(alias_df, distance_measure, max_distance_threshold, dists=None):
    if dists is None:
        dists = compute_distances(alias_df, distance_measure)
    # perform hierarchical clustering based on distances
    Z = scipy.cluster.hierarchy.linkage(dists, method="complete")
    # return clusters based on a threshold t
    clusters = scipy.cluster.hierarchy.fcluster(Z, t=max_distance_threshold, criterion="distance")
    # assign cluster ids to original alias df
    alias_df["cluster"] = clusters

    return alias_df, Z


# distance measures
def relative_lcs(A, B):
    return 1 - pylcs.lcs2(A, B) / max(len(A), len(B))


def lcs_distance(A, B):
    lcs = pylcs.lcs2(A, B)
    if lcs == 0:
        return 1
    else:
        return 1 / lcs


def relative_levenshtein(A, B):
    levdist = pylcs.levenshtein_distance(A, B)
    return levdist / max(len(A), len(B))


def relative_damerau_levenshtein(A, B):
    dalevdist = damerau_levenshtein_distance(A, B)
    return dalevdist / max(len(A), len(B))


def relative_hamming(A, B):
    hammdist = hamming_distance(A, B)
    return hammdist / max(len(A), len(B))


def jaro_distance(A, B):
    return 1 - jaro_similarity(A, B)


def jaro_winkler_distance(A, B):
    return 1 - jaro_winkler_similarity(A, B)


def get_same_asn_clusters(cluster_df, node_ips, whois_data):
    clusters_with_asn = cluster_df.merge(node_ips, how="left").merge(whois_data, how="left")
    clusters_with_asn = clusters_with_asn.dropna()  # remove .onion and aliases without known IP
    same_asn_clusters = clusters_with_asn.groupby("cluster") \
        .filter(lambda x: (x["asn"].nunique() == 1) & (x["pub_key"].nunique() > 1)) \
        .sort_values("cluster")
    return same_asn_clusters


def evaluate_single_result(clustered_alias_df, node_ips, whois_data):
    # clustered_alias_df consists of [pub_key, alias, cluster]
    # based on the pub_keys it is merged with node ips and whois data to filter to same ASN clusters
    # returned are statistics about cluster counts of size >1, >2 and >=26 (LNBIG)
    clusters = get_same_asn_clusters(clustered_alias_df, node_ips, whois_data)[["pub_key", "cluster"]].drop_duplicates()

    node_count = len(clusters)
    cluster_count = len(clusters.groupby("cluster").filter(
        lambda x: len(x) > 1).groupby("cluster").count())
    cluster_count_min3 = len(clusters.groupby("cluster").filter(
        lambda x: len(x) > 2).groupby("cluster").count())
    cluster_count_min26 = len(clusters.groupby("cluster").filter(
        lambda x: len(x) >= 26).groupby("cluster").count())

    return(pd.Series({"node_count": node_count,
                      "cluster_count": cluster_count,
                      "cluster_count_min3": cluster_count_min3,
                      "cluster_count_min26": cluster_count_min26}))


def evaluate_measure(alias_df, node_ips, whois_data, dist_measure, thresholds):
    # cluster a set of aliases based on a distance measure
    # merge with node_ips and whois_data to filter to same ASN clusters
    # produce statistics for a range of thresholds for the distance measure

    dists = compute_distances(alias_df, dist_measure)
    df = pd.DataFrame({"measure": dist_measure.__name__.replace("_", " "), "threshold": thresholds})
    # TODO Friedhelm: expected type 'function', got 'Series' instead
    stats = df.apply(lambda x:
                     evaluate_single_result(
                         cluster(alias_df.copy(), dist_measure,
                                 x["threshold"], dists)[0], node_ips, whois_data),
                     axis=1)
    result = pd.concat([df, stats], axis=1)
    print("Finished", dist_measure.__name__)
    return result

import pandas as pd

def make_cluster_aliases(nodeClustering):

    # Define functions to collapse multiple alias names
    def lcs(S,T):
        m = len(S)
        n = len(T)
        counter = [[0]*(n+1) for x in range(m+1)]
        longest = 0
        lcs_set = set()
        for i in range(m):
            for j in range(n):
                if S[i] == T[j]:
                    c = counter[i][j] + 1
                    counter[i+1][j+1] = c
                    if c > longest:
                        lcs_set = set()
                        longest = c
                        lcs_set.add(S[i-c+1:i+1])
                    elif c == longest:
                        lcs_set.add(S[i-c+1:i+1])

        return lcs_set

    def multilcs(aliases):
        aliases = sorted(aliases)
        mylcs = aliases[0]
        aliases = aliases[1:]
        before = ""
        after = ""
        while(len(aliases) > 0):
            try:
                newlcs = list(lcs(mylcs, aliases[0]))[0]
                if(len(newlcs) >= 3):
                    mylcs = newlcs
                index = aliases[0].index(mylcs)
                if(index > 0):
                    before = "*"
                if(len(aliases[0]) > (index + len(mylcs))):
                    after = "*"
                aliases = aliases[1:]
            except:
                break#pass#return(before+mylcs+after) # if not all words share a common prefix
        mylcs = mylcs.encode('ascii', 'ignore').decode('ascii')
        if(len(mylcs) > 15):
            return(before+mylcs[0:15]+"...")
        else:
            return(before+mylcs+after)


    entities = nodeClustering.groupby("cluster").agg(
        {"pub_key":len, "alias": lambda x: multilcs(map(str, x))}
    ).reset_index().sort_values("pub_key", ascending=False)
    entities = entities.rename(columns={"pub_key":"cluster_size"}).reset_index(drop=True)
    return(entities)
