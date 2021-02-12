# On-Chain Data Collection
In the following steps, we fetch funding and settlement transactions and addresses starting from the list of channels in `channel.csv` and then we map addresses to entities.
## 1. Txs and Addresses Collection
`01_txs_and_addresses_collection.ipynb` allows you to collect

- funding and settlement transactions
- funding and settlement addresses
- clean and store the data as csv and json files

## 2. Compute Entities
`02_compute_entities.sc` allows you to 

- map BTC addresses to entities using Spark and GraphSense
- compute relationships between entities
- compute entity stats and tags

## 3. Fetch Entities from HDFS
`03_fetch_entities_from_HDFS.py` allows you to

- retrieve the outputs of the previous step
- write the data into csv files