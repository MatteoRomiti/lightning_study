# Source Code

Here you find python and scala scripts, as well as jupyter notebooks and Rmd.

Each folder allows you to perform specific tasks in the pipeline and should be executed sequentially.

`utils.py` and `api_calls.py` are additional modules used by the rest of the code.

The steps are:

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
