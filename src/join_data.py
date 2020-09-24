# This script merges two datasets obtained with the
# describegraph command from two different LND nodes.

import pandas as pd

input_dir_1 = '../data/friedhelm/'
input_dir_2 = '../data/peter/'
input_file_1 = input_dir_1 + 'address_state.csv'
input_file_2 = input_dir_1 + 'edge_state.csv'
input_file_3 = input_dir_1 + 'node_state.csv'
input_file_4 = input_dir_2 + 'address_state_1582535881.csv'
input_file_5 = input_dir_2 + 'edge_state_1582535881.csv'
input_file_6 = input_dir_2 + 'node_state_1582535881.csv'

output_dir = '../data/joined/level_2/'


friedhelm_data = dict()
friedhelm_data['ip_address'] = pd.read_csv(input_file_1)
friedhelm_data['channel'] = pd.read_csv(input_file_2)
friedhelm_data['node'] = pd.read_csv(input_file_3).dropna()

peter_data = dict()
peter_data['ip_address'] = pd.read_csv(input_file_4).dropna()
peter_data['ip_address'] = peter_data['ip_address'].rename(columns={'IP_address': 'ip_address'})
peter_data['channel'] = pd.read_csv(input_file_5)
peter_data['node'] = pd.read_csv(input_file_6).dropna()

joined_data = dict()

friedhelm_data['ip_address'] = friedhelm_data['ip_address'].groupby('pub_key')['ip_address'].apply(lambda x: set(x)).reset_index()
peter_data['ip_address'] = peter_data['ip_address'].groupby('pub_key')['ip_address'].apply(lambda x: set(x)).reset_index()

j = friedhelm_data['ip_address'].merge(friedhelm_data['ip_address'], how='outer', on='pub_key')
j['ip_address'] = j.apply(lambda x: '|'.join(x[1].union(x[2])), axis=1)
joined_data['ip_address'] = j.drop(columns=['ip_address_x', 'ip_address_y'])

friedhelm_data['node'] = friedhelm_data['node'].groupby('pub_key')['alias'].apply(lambda x: set(x)).reset_index()
peter_data['node'] = peter_data['node'].groupby('pub_key')['alias'].apply(lambda x: set(x)).reset_index()

j = friedhelm_data['node'].merge(friedhelm_data['node'], how='outer', on='pub_key')
j['alias'] = j.apply(lambda x: '|'.join(x[1].union(x[2])), axis=1)
joined_data['node'] = j.drop(columns=['alias_x', 'alias_y'])

j = friedhelm_data['channel'].merge(peter_data['channel'], how='outer', on='chan_point')
j['node1_pub'] = j.apply(lambda x: x['node1_pub_x'] if isinstance(x['node1_pub_x'], str) else x['node1_pub_y'], axis=1)
j['node2_pub'] = j.apply(lambda x: x['node2_pub_x'] if isinstance(x['node2_pub_x'], str) else x['node2_pub_y'], axis=1)
joined_data['channel'] = j.drop(columns=['node1_pub_x', 'node1_pub_y', 'node2_pub_x', 'node2_pub_y', 'capacity'])

for k in joined_data:
    path = output_dir + k + '.csv'
    joined_data[k].to_csv(path, index=False)
