import requests
import json
from config import API_TOKEN  # ask Matteo to get one

# api_path = 'https://api.graphsense.info/'
api_path = 'http://localhost:5000/'
headers = {'Accept': 'application/json', 'Authorization': API_TOKEN}


def url2dict(url):
    # print(url)
    for i in range(4):  # allow some failures
        r = requests.get(url, headers=headers)
        d = json.loads(r.text)
        if 'message' not in d:
            return d
    return d

##############################
# API CALLS
# **** WARNING ****: 
# Most of these calls are not up-to-date with the latest API and fail 
# I'm slowly updating them.
# Look at https://api.graphsense.info/ to see current API docs
##############################

def get_label(label):
    url = api_path  + '/labelsearch?q=' + label
    return url2dict(url)


def get_address_info(address, currency='btc'):
    url = api_path + currency + '/' + 'addresses/' + address
    return url2dict(url)


def get_address_entityID(address, currency='btc'):
    address = str(address)
    url = api_path + currency + '/' + 'addresses/' + address + '/entity'
    d = url2dict(url)
    if d and 'entity' in d:
        entityID = d['entity']
        return entityID
    return None


def get_address_tags(address, currency='btc'):
    address = str(address)
    url = api_path + currency + '/' + 'addresses/' + address + '/tags'
    d = url2dict(url)
    if d:
        tags = list(set([el['label'] for el in d]))
        return tags
    return []


def get_address_tag(address, currency='btc'):
    tag = 'unknown'
    tags = get_address_tags(address, currency=currency)
    if tags:
        tag = tags[0]
    return tag


def get_address_txs(address, currency='btc'):
    url = api_path + currency + '/addresses/' + address
    d = url2dict(url)
    return d


def get_address_txs_out(address, currency='btc'):
    txs = get_address_txs(address, currency=currency)
    tx_hashes_out = set()
    for tx in txs:
        if tx['value']['value'] < 0:
            tx_hashes_out.add(tx['tx_hash'])
    return tx_hashes_out


def get_address_txs_out(address, currency='btc'):
    txs = get_address_txs(address, currency=currency)
    tx_hashes_out = set()
    for tx in txs:
        if tx['value']['value'] > 0:
            tx_hashes_out.add(tx['tx_hash'])
    return tx_hashes_out


def get_address_neighbors_out(address, currency='btc', limit=0):
    # get all addresses receiving money from this address which means:
    # scan all edges and if source==address, select the target
    address = str(address)
    if not limit:
        limit = get_address_n_transactions_out(address, currency=currency)
        if not limit:
            return {}
    url = api_path + currency + '/' + 'address/' + address + '/neighbors?direction=out&limit=' + str(limit)
    d = url2dict(url)
    neighbors_out = set()
    if d:
        for e in d['edges']:
            if e['source'] == address:
                neighbors_out.add(e['target'])
    return neighbors_out


def get_address_neighbors_in(address, currency='btc', limit=0):
    # get all addresses sending money to this address which means:
    # scan all edges and if target==address, select the source
    address = str(address)
    if not limit:
        limit = get_address_n_transactions_in(address, currency=currency)
        if not limit:
            return {}
    url = api_path + currency + '/' + 'address/' + address + '/neighbors?direction=in&limit=' + str(limit)
    d = url2dict(url)
    neighbors_in = set()
    if d:
        for e in d['edges']:
            if e['target'] == address:
                neighbors_in.add(e['source'])
    return neighbors_in


def get_address_neighbors(address, currency='btc', limit=0):
    limit = int(limit/2)  # because we do a union later
    neighbors_in = get_address_neighbors_in(address, currency=currency, limit=limit)
    neighbors_out = get_address_neighbors_out(address, currency=currency, limit=limit)
    return neighbors_out.union(neighbors_in)


def get_address_money_in(address, currency='btc', coin='satoshi'):
    money = 0
    info = get_address_info(address, currency=currency)
    if 'total_received' in info.keys():
        money = info['total_received'][coin]
    return money


def get_address_money_out(address, currency='btc', coin='satoshi'):
    money = 0
    info = get_address_info(address, currency=currency)
    if 'total_spent' in info.keys():
        money = info['total_spent'][coin]
    return money


def get_address_n_transactions(address, currency='btc'):
    return get_address_n_transactions_out(address, currency=currency) + get_address_n_transactions_in(address, currency=currency)


def get_address_n_transactions_out(address, currency='btc'):
    n = 0
    info = get_address_info(address, currency=currency)
    if 'no_outgoing_txs' in info.keys():
        n = info['no_outgoing_txs']
    return n


def get_address_n_transactions_in(address, currency='btc'):
    n = 0
    info = get_address_info(address, currency=currency)
    if 'no_incoming_txs' in info.keys():
        n = info['no_incoming_txs']
    return n


def get_address_balance(address, currency='btc', coin='eur'):
    balance = 0
    info = get_address_info(address, currency=currency)
    if info:
        balance = info['balance'][coin]
    return balance


def get_address_received(address, currency='btc', coin='eur'):
    received = 0
    info = get_address_info(address, currency=currency)
    if info:
        received = info['total_received'][coin]
    return received


def get_entity_info(entity, currency='btc'):
    url = api_path + currency + '/' + 'entities/' + str(entity)
    return url2dict(url)


def get_entity_addresses(entity, currency='btc', page_size=10000):
    url = api_path + currency + '/' + 'entities/' + str(entity) + '/addresses?pagesize=' + str(page_size)
    res = url2dict(url)
    if 'addresses' in res:
        return [el['address'] for el in res['addresses']]
    else:
        return res


def get_entity_tags(entity, currency='btc'):
    url = api_path + currency + '/' + 'entities/' + str(entity) + '/tags'
    d = url2dict(url)
    if d:
        tags = list(set([el['label'] for el in d]))
        return tags
    return ['Unknown']

# def get_entity_tags_csv(entity, currency='btc'):
#     url = api_path + currency + '/' + 'entities/' + str(entity) + '/tags.csv'
#     d = url2dict(url)
#     if d:
#         tags = list(set([el['label'] for el in d]))
#         return tags
#     return ['Unknown']


def get_entity_tag(entity, currency='btc'):
    tag = 'Unknown'
    tags = get_entity_tags(entity, currency=currency)
    if tags:
        tag = tags[0]
    return tag


def get_entity_n_neighbors_out(entity, currency='btc'):
    n = 0
    info = get_entity_info(entity, currency=currency)
    if 'out_degree' in info.keys():
        n = info['out_degree']
    return n


def get_entity_n_neighbors_in(entity, currency='btc'):
    n = 0
    info = get_entity_info(entity, currency=currency)
    if 'in_degree' in info.keys():
        n = info['in_degree']
    return n


def get_entity_neighbors_out(entity, currency='btc', limit=0):
    # get all entities receiving money from this entity which means:
    # scan all edges and if source==entity, select the target
    neighbors_out = set()
    if not limit:
        limit = get_entity_n_transactions_out(entity, currency=currency)
        if not limit:
            return neighbors_out
    url = api_path + currency + '/' + 'entities/' + str(entity) + '/neighbors?direction=out&limit=' + str(limit)
    d = url2dict(url)
    if d:
        for e in d['edges']:
            if e['source'] == entity:
                neighbors_out.add(e['target'])
    return neighbors_out


def get_entity_neighbors_in(entity, currency='btc', limit=0):
    # get all entities sending money to this entity which means:
    # scan all edges and if target==entity, select the source
    neighbors_in = set()
    if not limit:
        limit = get_entity_n_transactions_out(entity, currency=currency)
        if not limit:
            return neighbors_in
    url = api_path + currency + '/' + 'entities/' + str(entity) + '/neighbors?direction=in&limit=' + str(limit)
    d = url2dict(url)
    neighbors_in = set()
    if d:
        for e in d['edges']:
            if e['target'] == entity:
                neighbors_in.add(e['source'])
    return neighbors_in


def get_entity_neighbors(entity, currency='btc', limit=0):
    limit = int(limit/2)
    neighbors_in = get_entity_neighbors_in(entity, currency=currency, limit=limit)
    neighbors_out = get_entity_neighbors_out(entity, currency=currency, limit=limit)
    return neighbors_out.union(neighbors_in)


def get_entity_n_transactions(entity, currency='btc'):
    return get_entity_n_transactions_out(entity, currency=currency) + get_entity_n_transactions_out(entity)


def get_entity_n_transactions_out(entity, currency='btc'):
    n = 0
    info = get_entity_info(entity, currency=currency)
    if 'no_outgoing_txs' in info.keys():
        n = info['no_outgoing_txs']
    return n


def get_entity_n_transactions_in(entity, currency='btc'):
    n = 0
    info = get_entity_info(entity, currency=currency)
    if 'no_incoming_txs' in info.keys():
        n = info['no_incoming_txs']
    return n


def get_entity_balance(entity, currency='btc', coin='eur'):
    balance = 0
    info = get_entity_info(entity, currency=currency)
    if info:
        balance = info['balance'][coin]
    return balance


def get_entity_received(entity, currency='btc', coin='eur'):
    received = 0
    info = get_entity_info(entity, currency=currency)
    if info:
        received = info['total_received'][coin]
    return received


def get_entity_n_addresses(entity, currency='btc'):
    n_addresses = 0
    info = get_entity_info(entity, currency=currency)
    if info:
        n_addresses = info['no_addresses']
    return n_addresses


def get_entity_txs_timestamps(entity, currency='btc'):
    # returns a list of transaction timestamps for a entity (or address)
    tss = []
    # get all entity addresses txs
    addresses = get_entity_addresses(entity , currency=currency, limit=get_entity_info(entity, currency=currency)['no_addresses'])
    # for each address get txs_ts and append them
    for address in addresses:
        txs = get_address_txs(address, currency=currency, limit=get_address_n_transactions(address, currency=currency)+1)
        tmp = [el['timestamp'] for el in txs]
        for t in tmp:
            tss.append(t)
    return tss

# TODO:
# def get_entity_n_neighbors_in()
# def get_entity_n_neighbors_out()
# def get_entity_n_neighbors()
# def get_entity_txs()
# def get_entity_txs_out()
# def get_entity_txs_in()


def get_tx(tx_hash, currency='btc'):
    url = api_path + currency + '/' + 'txs/' + tx_hash
    return url2dict(url)


def get_tx_addresses_in(tx_hash, currency='btc'):
    tx = get_tx(tx_hash, currency=currency)
    if 'inputs' in tx:
        return [el['address'] for el in tx['inputs']]
    return []


def get_tx_addresses_out(tx_hash, currency='btc'):
    tx = get_tx(tx_hash, currency=currency)
    addresses_out = [el['address'] for el in tx['outputs']]
    return addresses_out


def get_tx_entity_in(tx_hash, currency='btc'):
    address_in = get_tx_addresses_in(tx_hash, currency=currency)
    if address_in:
        return get_address_entityID(address_in[0], currency=currency)
    return -1


def get_tx_entities_out(tx_hash, currency='btc'):
    entities_out = [get_address_entityID(addr, currency=currency) for addr in get_tx_addresses_out(tx_hash, currency=currency)]
    return entities_out


def get_tx_tags_in(tx_hash, currency='btc'):
    tags_in = [get_address_tag(addr, currency=currency) for addr in get_tx_addresses_in(tx_hash, currency=currency)]
    return tags_in


def get_tx_tags_out(tx_hash, currency='btc'):
    tags_out = [get_address_tag(addr, currency=currency) for addr in get_tx_addresses_out(tx_hash, currency=currency)]
    return tags_out


def get_tx_values_out(tx_hash, currency='btc', coin='eur'):
    return [el['value'][coin] for el in get_tx(tx_hash, currency=currency)['outputs']]


def get_tx_values_in(tx_hash, currency='btc', coin='eur'):
    return [el['value'][coin] for el in get_tx(tx_hash, currency=currency)['inputs']]


def get_addresses_txs(addresses, currency='btc', direction='both'):
    addresses_txs = dict()  # key: address, value: list of txs
    ln = len(addresses)
    addresses = list(addresses)
    addresses.sort()
    for i, addr in enumerate(addresses):
        print(ln, i, addr, end='\r')
        if direction == 'in':
            addresses_txs[addr] = [get_tx(hsh, currency=currency) for hsh in get_address_txs_in(addr, currency=currency)]
        if direction == 'out':
            addresses_txs[addr] = [get_tx(hsh, currency=currency) for hsh in get_address_txs_out(addr, currency=currency)]
        if direction == 'both':
            addresses_txs[addr] = [get_tx(hsh, currency=currency) for hsh in get_address_txs(addr, currency=currency)]
    return addresses_txs


def get_block_hash(height, currency='btc'):
    url = api_path + currency + '/' + 'block/' + str(height)
    return url2dict(url)['block_hash']

def get_block_n_txs(height, currency='btc'):
    url = api_path + currency + '/' + 'block/' + str(height)
    return url2dict(url)['no_txs']
