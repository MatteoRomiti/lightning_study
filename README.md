# Lightning Study

## How to

In what follows, we present the steps we took in order to produce the results
in the paper. Some steps rely on the [GraphSense API][GS API]. You may choose
to get an API token to query on-chain data running our scripts or use the data
we already fetched and stored in `data/joined/level_1` and
`data/joined/level_2`.

#### Requirements

- python3
- [`git lfs`][git lfs]
- `pip install -r requirements.txt`
- [optional] an API token for [GraphSense][GS API]

Below the steps needed to reproduce the results.

#### Get LN data

Run an [LND][LND] node and export the LN graph using the `describegraph`
command every 30 minutes.

Split data into `channel.csv`, `ip_address.csv` and `node.csv` and place them
in `data/joined/level_2`.

#### Get funding and settlement txs

Use the channel points in `channel.csv` to get the details of the funding
transactions by querying the [GraphSense API][GS API] and store the
results in `data/joined/level_1/funding_txs.json`:

    python3 get_funding_txs.py

Use the funding transactions and the channel points to get the details of the
settlement transactions and the settlement addresses by querying the
[GraphSense API][GS API] and store the results in
 `data/joined/level_1/funded_address_settlement_txs.json` and
 `data/joined/level_1/settlement_addresses.json`:

    python3 get_funded_address_settlement_txs.py

#### Get mapping of funding and settlement address to entities

Map funding and settlement addresses to funding and settlement entities by
querying the [GraphSense API][GS API] and store the results in
`data/joined/level_1/funding_address_entity.json` and
`data/joined/level_1/settlement_address_entity.json`:

    python3 get_funding_address_entity.json
    python3 get_settlement_address_entity.json

#### Perform on-chain clustering heuristics

Use the funding and settlement entities to retrieve source and destination
entities by querying the [GraphSense API][GS API]:

    ...

Cluster source, funding, settlement and destination entities into components
(star, snake, collector and proxy).

    ...

#### Perform off-chain clustering heuristics

Use aliases and IP addresses to cluster nodes (note that this takes several hours):

    python3 alias_asn_ip_clustering_heuristic.py

#### Perform cross-layer linking heuristics

Sort stars, snakes and proxies and assign them unique IDs:

    python3 sort_mapping_entities.py

Find channel points that use coins from settlement transactions:

    python3 get_reused_coins_txs.py

    
Use results from on-chain clustering heuristics to link Bitcoin entities to LN
nodes. Two linking heuristics are available.

    python3 LN_BTC_heuristic_1.py
    python3 LN_BTC_heuristic_2.py

The results are stored in `data/joined/results/`. In particular,
`filtered_heuristic_2_results.json` and `filtered_heuristic_2_results.json`
report absolute and relative numbers of linked entities and nodes, while
`*_entity_node.json` and `*_node_entity.json` contain the actual links (from
entity to node and vice versa). On-chain patterns used before the linking
heuristics are mentioned in the file name, e.g.,
`star_heuristic_1_entity_node.json` contains the mapping from entity to node
using the star-pattern on top of the standard multi-input clustering heuristic.
When `filtered_` is prepended to the file name, it means that, to the best of
our knowledge, no exchanges or similar services are in the dataset (please,
refer to the paper for further details).

Check the linking overlap between the two heuristics:

    python3 check_linking_overlap.py

Check how many "questionable" attributions are created by the second
heuristic by using on-chain activity time overlap of nodes:

    python3 check_time_overlap.py

Use the off-chain clustering heuristic to see how many Bitcoin addresses can be
attributed with an LN attribution tag:

    python3 linking_alias_overlap.py


#### Perform attacks on the LN

Use the results of the LN node clustering heuristic to evaluate the security
and privacy of the LN:

    ...

---

### Notes
- keyspace used: `btc_transformed_20200224_dev` (last block height: 618857)
- An API token for GraphSense is needed to query on-chain data

[arxiv]: https://arxiv.org/abs/2007.00764
[git lfs]: https://git-lfs.github.com/
[LND]: https://github.com/lightningnetwork/lnd
[GS API]: https://api.graphsense.info/
[BS API]: https://github.com/Blockstream/esplora/blob/master/API.md
