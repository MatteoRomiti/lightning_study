# Lightning Study

In what follows, we present the steps we took in order to produce the results
in the [paper][arxiv]. Some steps rely on the [GraphSense API][GS API] and some
others on Spark jobs running on a GraphSense cluster.

**Note** that you may choose to run all the notebooks (API token needed) or
use the data we already fetched and stored in `data/level_1` and
`data/level_2`.

## Requirements

- python3
- jupyter notebook
- [`git lfs`][git lfs] (data will be later hosted on zenodo)
- `pip install -r requirements.txt`
- [optional] an API token for [GraphSense][GS API]
- [optional] GraphSense instance for Spark jobs

## Pipeline
You can open each notebook and follow the instructions, run cells, play with 
the data and reproduce and check the results.  
### 1. Data Collection
Fetch funding and settlement transactions and addresses starting from a list of 
LN channels.
### 2. On-Chain Clustering
Cluster BTC entities based on their interaction with the LN and produce a
mapping between entities and components (stars, snakes, collectors, proxies).
### 3. Off-Chain Clustering
Cluster LN nodes based on their aliases and IP information using different 
metrics. 
### 4. Linking
Link BTC entities to LN nodes with two linking heuristics and compare the 
results with ground truth data we collected.

[arxiv]: https://arxiv.org/abs/2007.00764
[git lfs]: https://git-lfs.github.com/
[LND]: https://github.com/lightningnetwork/lnd
[GS API]: https://api.graphsense.info/
[BS API]: https://github.com/Blockstream/esplora/blob/master/API.md
