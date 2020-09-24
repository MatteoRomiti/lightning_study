# This script maps IDs of stars, snakes, proxies into
# a sorted list of unique IDs

import pandas as pd
from utils import write_json

input_dir = '../data/joined/results/'
relaxed = False

star_file = input_dir + 'funding_cluster_star_pattern_filtered_relaxed.csv'
snake_file = input_dir + 'funding_cluster_snake_pattern_filtered_relaxed.csv'
collector_file = input_dir + 'settlement_cluster_collector_pattern_filtered_relaxed.csv'
proxy_file = input_dir + 'settlement_cluster_collector_pattern_extended_filtered_relaxed.csv'

if not relaxed:
    star_file = input_dir + 'funding_cluster_star_pattern_filtered.csv'
    snake_file = input_dir + 'funding_cluster_snake_pattern_filtered.csv'
    collector_file = input_dir + 'settlement_cluster_collector_pattern_filtered.csv'
    proxy_file = input_dir + 'settlement_cluster_collector_pattern_extended_filtered.csv'


output_dir = '../data/joined/results/'
output_file1 = output_dir + 'star_sorted_mapping.json'
output_file2 = output_dir + 'snake_sorted_mapping.json'
output_file3 = output_dir + 'collector_sorted_mapping.json'
output_file4 = output_dir + 'proxy_sorted_mapping.json'

print('relaxed:', relaxed)

stars_df = pd.read_csv(star_file)
snakes_df = pd.read_csv(snake_file)
collectors_df = pd.read_csv(collector_file)
proxies_df = pd.read_csv(proxy_file)


def df_to_two_dicts(components_df):
    entity_component = dict()
    component_entities = dict()
    for e in components_df.values:
        cluster, entity = e
        if cluster not in component_entities:
            component_entities[cluster] = []
        component_entities[cluster].append(entity)
        entity_component[entity] = cluster
    return entity_component, component_entities


entity_snake, snake_entities = df_to_two_dicts(snakes_df)
entity_star, star_entities = df_to_two_dicts(stars_df)
entity_collector, collector_entities = df_to_two_dicts(collectors_df)
entity_proxy, proxy_entities = df_to_two_dicts(proxies_df)


if __name__ == '__main__':

    # # IMPORTANT: there is no entity overlap between stars, snakes and collectors
    print('overlap of entities snake-star:')
    print(len(set(entity_snake.keys()).intersection(set(entity_star.keys()))))
    print('overlap of entities proxy-star:')
    print(len(set(entity_proxy.keys()).intersection(set(entity_star.keys()))))
    print('overlap of entities snake-proxy:')
    print(len(set(entity_proxy.keys()).intersection(set(entity_snake.keys()))))
    print('overlap of entities snake-collector:')
    print(len(set(entity_collector.keys()).intersection(set(entity_snake.keys()))))
    print('overlap of entities proxy-collector:')
    print(len(set(entity_collector.keys()).intersection(set(entity_proxy.keys()))))

    i = 1  # to avoid negative zero
    star_sorted_mapping = dict()
    for star in star_entities:
        star_sorted_mapping[star] = i
        i += 1
    print('stars till', i)

    snake_sorted_mapping = dict()
    for snake in snake_entities:
        snake_sorted_mapping[snake] = i
        i += 1
    print('snakes till', i)

    collector_sorted_mapping = dict()
    for collector in collector_entities:
        collector_sorted_mapping[collector] = i
        i += 1
    print('collectors till', i)

    proxy_sorted_mapping = dict()
    for proxy in proxy_entities:
        proxy_sorted_mapping[proxy] = i
        i += 1
    print('proxies till', i)

    write_json(star_sorted_mapping, output_file1, True)
    write_json(snake_sorted_mapping, output_file2, True)
    write_json(collector_sorted_mapping, output_file3, True)
    write_json(proxy_sorted_mapping, output_file4, True)
