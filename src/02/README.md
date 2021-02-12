# On-Chain Clustering
In the following steps, we perform on-chain clustering heuristics based on the output files of the previous steps.

## 1. Map entities
`01_analysis_level_1.Rmd` allows you to 

- map funding and settlement entities into components (stars, snakes, collectors, proxies) 
- files useful for visualization on gephi

## 2. Check and Sort Components
`02_check_sort_components.ipynb` allows you to 

- check that there is no overlap among clustered entities
- assign a unique and sorted ID to each component

