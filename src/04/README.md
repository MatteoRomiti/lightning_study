# Linking and Ground Truth

In the following steps, we link entities to nodes, collect ground truth and validate the results.
## 1. Linking
`01_linking.ipynb` allows you to
- perform Linking Heuristic 1
- perform Linking Heuristic 2
- validate the results (using data from step 2 "Ground Truth Collection" below)
- combine Linking and Alias/IP-based Heuristics

## 2. Ground Truth Collection
`02_ground_truth_collection.ipynb` contains the code to 

- create a list of Target Nodes, nodes to be validated
- collect Ground Truth data to validate links

Note that this step requires interaction with the LND client.