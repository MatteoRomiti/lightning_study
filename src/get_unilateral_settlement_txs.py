# This script fetches settlement tx details from the blockstream API and
# selects the unilateral closes

from utils import write_json, get_blockstream_tx, level1_folder
from load_data import settlement_txs_hashes

output_file = level1_folder + 'unilateral_settlement_txs.json'

unilateral_settlement_txs = dict()
for tx in settlement_txs_hashes:
    unilateral_settlement_txs[tx] = None

for i, tx in enumerate(settlement_txs_hashes):
    print(i, end='\r')
    try:
        if not unilateral_settlement_txs[tx]:
            d = get_blockstream_tx(tx)
            unilateral_settlement_txs[tx] = d
    except Exception as e:
        print(e)
        write_json(unilateral_settlement_txs, output_file)

write_json(unilateral_settlement_txs, output_file)
