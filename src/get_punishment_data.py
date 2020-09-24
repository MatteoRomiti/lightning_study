# This script gets data for creating a list of settlement txs with punishment
# tx, starting from a list of settlement txs

from utils import read_json, write_json, get_blockstream_tx, level1_folder, get_blockchain_page, get_outputs_spenders
from load_data import funded_address_settlement_txs

input_file1 = level1_folder + 'possible_two_output_unilateral_settlement_txs.json'
input_file2 = level1_folder + 'unilateral_settlement_txs_page.json'
input_file3 = level1_folder + 'spender_details.json'

output_file1 = input_file1
output_file2 = input_file2
output_file3 = input_file3
output_file4 = level1_folder + 'spender_address_btc.json'

settlement_txs_dict = dict()
for stxs in funded_address_settlement_txs.values():
    if stxs:
        for stx in stxs:
            stx_hash = stx['tx_hash']
            settlement_txs_dict[stx_hash] = stx

# select settlement txs with two outputs
possible_two_output_unilateral_settlement_txs_hashes = []
for tx in settlement_txs_dict.values():
    if len(tx['outputs']) == 2:
        possible_two_output_unilateral_settlement_txs_hashes.append(tx['tx_hash'])

# get tx details from blockstream
try:
    possible_two_output_unilateral_settlement_txs = read_json(input_file1)
except Exception as e:
    possible_two_output_unilateral_settlement_txs = dict()
    for tx in possible_two_output_unilateral_settlement_txs_hashes:
        possible_two_output_unilateral_settlement_txs[tx] = None
for i, tx in enumerate(possible_two_output_unilateral_settlement_txs_hashes):
    print(i, end='\r')
    if not possible_two_output_unilateral_settlement_txs[tx]:
        d = get_blockstream_tx(tx)
        possible_two_output_unilateral_settlement_txs[tx] = d
write_json(possible_two_output_unilateral_settlement_txs, output_file1)

# select unilateral close with p2wsh output
double_p2wsh = 0
p2wsh_outputs = set()  # tx_hash:out_index
n_p2wsh = 0
unilateral_settlement_txs_with_p2wsh_in_outputs = []
for t in possible_two_output_unilateral_settlement_txs.values():
    seq = t['vin'][0]['sequence']
    if seq != 4294967295:
        # unilateral
        n_p2wsh_in_tx = 0
        for i, vout in enumerate(t['vout']):
            if vout['scriptpubkey_type'] == 'v0_p2wsh':
                p2wsh_outputs.add(t['txid'] + ':' + str(i))
                n_p2wsh_in_tx += 1
        if n_p2wsh_in_tx:
            unilateral_settlement_txs_with_p2wsh_in_outputs.append(t['txid'])
        if n_p2wsh_in_tx == 2:
            double_p2wsh += 1
        n_p2wsh += n_p2wsh_in_tx
# print('Out of', len(possible_two_output_unilateral_settlement_txs_hashes), 'two-output settlement txs, we have', unilateral_seq, 'unilateral closes and', double_p2wsh, 'of them have p2wsh in both outputs')

# get txs spending these outputs
# to do this, first query blockchain.com/explorer to get the entire page
# containing the tx hashes of the spenders then select the p2wsh spenders
try:
    hash_page = read_json(output_file2)
except Exception as e:
    hash_page = dict()
    for tx_hash in unilateral_settlement_txs_with_p2wsh_in_outputs:
        hash_page[tx_hash] = None
for i, tx in enumerate(hash_page):
    print(i, end='\r')
    if not hash_page[tx]:
        page = get_blockchain_page(tx)
        hash_page[tx] = page
write_json(hash_page, output_file2)

unilateral_settlement_txs_with_p2wsh_in_outputs_spenders = dict()
for tx_hash in unilateral_settlement_txs_with_p2wsh_in_outputs:
    unilateral_settlement_txs_with_p2wsh_in_outputs_spenders[tx_hash] = get_outputs_spenders(tx_hash, hash_page)

try:
    spender_details = read_json(input_file3)
except Exception as e:
    spender_details = dict()  # spender tx hash and its details
    for stx in unilateral_settlement_txs_with_p2wsh_in_outputs_spenders:
        spenders = unilateral_settlement_txs_with_p2wsh_in_outputs_spenders[stx]
        for i, spender in enumerate(spenders): # two spender txs at most
            stx_out_index = stx + ':' + str(i)
            if stx_out_index in p2wsh_outputs:
                spender_details[spender] = None
    write_json(spender_details, output_file3)

for i, tx in enumerate(spender_details):
    print(i, end='\r')
    if not spender_details[tx]:
        details = get_blockstream_tx(tx)
        spender_details[tx] = details
write_json(spender_details, output_file3)

# for each spender I need not only the tx hash,
# but also the address and the amount to be more secure
spender_address_btc = set()  # spender tx hash + address + btc
for stx in unilateral_settlement_txs_with_p2wsh_in_outputs_spenders:
    spenders = unilateral_settlement_txs_with_p2wsh_in_outputs_spenders[stx]
    for i, spender in enumerate(spenders):  # two spender txs at most
        stx_out_index = stx + ':' + str(i)
        if stx_out_index in p2wsh_outputs:
            address = settlement_txs_dict[stx]['outputs'][i]['address']  # the output address of the settlement tx
            btc = settlement_txs_dict[stx]['outputs'][i]['value']['value']
            key = spender + ':' + address + ':' + str(btc)
            spender_address_btc.add(key)
write_json(list(spender_address_btc), output_file4)

