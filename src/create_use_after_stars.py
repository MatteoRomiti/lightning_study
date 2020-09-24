# This script creates a list of stars to be used after linking

from utils import results_folder, read_json, write_json
from sort_mapping_entities import relaxed
from apply_all_stars_after_linking import star_entities


output_file1 = results_folder + 'use_later_stars_1.json'
output_file2 = results_folder + 'use_later_stars_2.json'

if relaxed:
    results_folder += 'relaxed_filtered_'
else:
    results_folder += 'filtered_'

# use all clustering before:
# 	star-snake-collector-entity <--> nodes
heuristic_1_entity_node_all = read_json(results_folder + 'all_heuristic_1_entity_node.json', True)
heuristic_2_entity_node_all = read_json(results_folder + 'all_heuristic_2_entity_node_conf.json', double_int_key=True)[2]


# star_entities: star is positive and in {1,..., N1}
def create_use_later_stars(entity_node):
    use_later_stars = set()
    for star in star_entities:
        # if star not in mapping above, add it to use_later_stars
        if -star not in entity_node:
            use_later_stars.add(star)
    return list(use_later_stars)


use_later_stars_1 = create_use_later_stars(heuristic_1_entity_node_all)
use_later_stars_2 = create_use_later_stars(heuristic_2_entity_node_all)

write_json(use_later_stars_1, output_file1)
write_json(use_later_stars_2, output_file2)

# apply all clusterings but without use_later_stars:
#   pass the star blacklist to the mapping of the heuristics
# 	star-snake-collector-entity <--> nodes
# apply use_later_stars and see if you get new clusters
