# This script finds punishment txs starting from a list of settlement txs and
# then creates a list of settlement txs that cannot be used in the closing
# linking heuristic, assuming that the data collected by get_punishment_data.py
# is already available

from utils import read_json, write_json, level1_folder, results_folder

input_file1 = level1_folder + 'spender_address_btc.json'
input_file2 = level1_folder + 'spender_details.json'
input_file3 = level1_folder + 'possible_two_output_unilateral_settlement_txs.json'

output_file = results_folder + 'settlement_txs_with_punishment.json'

spender_address_btc = read_json(input_file1)
spender_details = read_json(input_file2)
possible_two_output_unilateral_settlement_txs = read_json(input_file3)

non_collaborative_settlement_address_btc = dict()
non_standard_witnesses = []
n_punishment_txs = 0
non_standard_witness_len = dict()
for sab in spender_address_btc:
    spender, address, btc = sab.split(':')
    details = spender_details[spender]  # cannot use spender_address_btc_details cause it has more keys
    for vin in details['vin']:
        if vin['prevout']['scriptpubkey_address'] == address and vin['prevout']['value'] == int(btc):
            len_witness = len(vin['witness'])
            if len_witness != 3:
                if len_witness not in non_standard_witness_len:
                    non_standard_witness_len[len_witness] = 0
                non_standard_witness_len[len_witness] += 1
                # print(details['txid'], 'non standard witness')
                non_standard_witnesses.append(vin['witness'])
#                 print(len(vin['witness']), end=' ')
            else:
                x = vin['witness'][1]
                if x:
                    # print(spender, x)
                    n_punishment_txs += 1
                    key = address + ':' + btc
                    if key not in non_collaborative_settlement_address_btc:
                        non_collaborative_settlement_address_btc[key] = 0
                    non_collaborative_settlement_address_btc[key] += 1

settlement_txs_with_punishment = set()
# for each settlement tx
for tx in possible_two_output_unilateral_settlement_txs:
    # if one output has a p2wsh and the address and the value are in non_collaborative_settlement_address_btc
        # add settlement tx to unusable
    for vout in possible_two_output_unilateral_settlement_txs[tx]['vout']:
        if vout['scriptpubkey_type'] == 'v0_p2wsh':
            key = vout['scriptpubkey_address'] + ':' + str(vout['value'])
            if key in non_collaborative_settlement_address_btc:
                settlement_txs_with_punishment.add(tx)

write_json(list(settlement_txs_with_punishment), output_file)
