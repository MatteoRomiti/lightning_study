# Cross-Layer Deanonymization Methods in the Lightning Protocol

In what follows, we present the steps we took in order to produce the results in this [paper][arxiv]. Some steps rely on the [GraphSense API][GS API] and some others on Spark jobs running on a GraphSense cluster, even though we still provide the resulting data.

You may choose to run all the cells in the notebooks or skip some by re-using the data we already fetched and stored or computed.

## Requirements

- python3 + jupyter notebook
- scala
- R
- get the data from Zenodo [here][zenodo] and place the `data` folder next to the `src` folder 
- `pip install -r requirements.txt`
- [optional] an API token for [GraphSense][GS API]
- [optional] GraphSense instance for Spark jobs

## Pipeline
You can open each notebook and follow the instructions, run cells, play with the data and reproduce and check the results.  
### 0. Off-Chain Data Collection
Collect snapshots of the Lightning Network by using *describegraph* from the [LND][LND] client and store the data in `data/level_2/` in three csv files: `channel.csv`, `node.csv`, `ip_address.csv`.
### 1. On-Chain Data Collection
Fetch funding and settlement transactions and addresses starting from the list of channels in `channel.csv`.
### 2. On-Chain Clustering
Cluster BTC entities based on their interaction with the LN and produce a mapping between entities and components (stars, snakes, collectors, proxies).
### 3. Off-Chain Clustering
Cluster LN nodes based on their aliases and IP information using different metrics.
### 4. Linking and Ground Truth
Link BTC entities to LN nodes with two linking heuristics and compare the results with ground truth data we collected.
### 5. Security and Privacy Analysis
Based on the knowledge of who created a channel, identify entities that own large capacity shares. Secondly, study attack potential based on the off-chain clustering. This includes griefing attacks, DoS, wormholes, value privacy and relationship anonymity.

### Notes
- keyspace used: `btc_transformed_20200909` (last block height: 618857)


[arxiv]: https://arxiv.org/abs/2007.00764
[git lfs]: https://git-lfs.github.com/
[LND]: https://github.com/lightningnetwork/lnd
[GS API]: https://api.graphsense.info/
[BS API]: https://github.com/Blockstream/esplora/blob/master/API.md
[zenodo]: https://zenodo.org/record/4482108