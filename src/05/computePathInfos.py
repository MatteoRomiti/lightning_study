import igraph as igraph
from igraph import *
import pandas as pd
from tqdm import tqdm
import sys

if(len(sys.argv) < 4):
    print("You need to pass exactly 4 parameters to this script.")
    print("1) a lightning network snapshot file")
    print("2) a lightning node cluster file")
    print("3) a satoshi amount")
    print("4) an output folder")
    print("Example: python computePathInfos.py lnsnapshot2020-09-09.csv alias_address_clusters.csv 100000 /tmp/results/")
    print("The resulting pkl file will be created in the current directory.")
    exit()
else:
    lnsnapshotFile = sys.argv[1]
    lightningNodeClustersFile = sys.argv[2]
    amount = int(sys.argv[3])
    outputFolder = sys.argv[4]

print("using snapshot", lnsnapshotFile)
print("using cluster file", lightningNodeClustersFile)
print("Using amount", amount)
outputFile = outputFolder + "".join(lnsnapshotFile.split("/")[-1].split(".")[:-1]) + "-" + str(amount)+"-sats.pkl"
print("Will create", outputFile, "This will take some time...")


edgelist = pd.read_csv(lnsnapshotFile)
edgelistTo = edgelist.copy().rename(columns={"node1_pub":"node1", "node2_pub":"node2"})
edgelistTo = edgelistTo[edgelistTo.capacity >= amount]
edgelistTo["fee"] = (edgelistTo["n2p.fee_base_msat"] + edgelistTo["n2p.fee_rate_milli_msat"] * amount / 1000) / 1000

edgelistFrom = edgelist.copy().rename(columns={"node1_pub":"node2", "node2_pub":"node1"})
edgelistFrom = edgelistFrom[edgelistFrom.capacity >= amount]
edgelistFrom["fee"] = (edgelistTo["n1p.fee_base_msat"] + edgelistTo["n1p.fee_rate_milli_msat"] * amount / 1000) / 1000

edgelist = pd.concat([
    edgelistFrom[["node1", "node2", "fee"]],
    edgelistTo[["node1", "node2", "fee"]]])

# Create an igraph object based on the edge list
tuples = [tuple(x) for x in edgelist.values]
g = igraph.Graph.TupleList(tuples, directed = True, edge_attrs = ['weight'])

# Functions to store, zero and restore a nodes outgoing edges
# This is needed because a lightning transaction through a channel of the source node is free
def get_multi_out_edge_properties(graph, node):
    edges = graph.vs.find(name=node).out_edges()
    result = dict(map(lambda x: (x.index, x.attributes()), edges))
    return(result)

def set_out_fees_to_zero(graph, node):
    edges = graph.vs.find(name=node).out_edges()
    for edge in edges:
        edge.update_attributes({"weight":0})

def restore_edge_properties(graph, properties):
    for key in properties:
        graph.es[key].update_attributes(properties[key])

# Compute the shortest paths with igraph, store source, intermediaries and target
result = list()
for node1 in tqdm(list(map(lambda v: v['name'], g.vs()))):
    props = get_multi_out_edge_properties(g, node1)
    set_out_fees_to_zero(g, node1)
    paths = list(map(lambda x: x,#g.vs[x]['name'],
                     g.get_shortest_paths(node1, None, mode=OUT, output='vpath', weights="weight")))
    for path in paths:
        if(len(path)==1):
            continue
        if(len(path) > 2):
            intermediaries = path[1:-1]
        else:
            intermediaries = []
        result.append({"source":path[0], "intermediaries":intermediaries, "target":path[-1]})
    restore_edge_properties(g, props)

print(len(result))
shortest_paths = pd.DataFrame(result)


# Define functions to collapse multiple alias names
def lcs(S,T):
    m = len(S)
    n = len(T)
    counter = [[0]*(n+1) for x in range(m+1)]
    longest = 0
    lcs_set = set()
    for i in range(m):
        for j in range(n):
            if S[i] == T[j]:
                c = counter[i][j] + 1
                counter[i+1][j+1] = c
                if c > longest:
                    lcs_set = set()
                    longest = c
                    lcs_set.add(S[i-c+1:i+1])
                elif c == longest:
                    lcs_set.add(S[i-c+1:i+1])

    return lcs_set

def multilcs(aliases):
    aliases = sorted(aliases)
    mylcs = aliases[0]
    aliases = aliases[1:]
    before = ""
    after = ""
    while(len(aliases) > 0):
        try:
            mylcs = list(lcs(mylcs, aliases[0]))[0]
            index = aliases[0].index(mylcs)
            if(index > 0):
                before = "*"
            if(len(aliases[0]) > (index + len(mylcs))):
                after = "*"
            aliases = aliases[1:]
        except:
            return(before+mylcs+after) # if not all words share a common prefix
    return(before+mylcs+after)

clusters = pd.read_csv(lightningNodeClustersFile)
clusters['alias'] = clusters['alias'].astype(str)

largest_entities = clusters.groupby("cluster").agg(
    {"pub_key":len, "alias": lambda x: multilcs(x)}
).reset_index().sort_values("pub_key", ascending=False)
largest_entities = largest_entities.rename(columns={"pub_key":"cluster_size"}).reset_index(drop=True)


# Create a mpping of vertex ids to names and names to vertex ids for future lookups
id_to_name = dict(map(lambda x: (x.index, x['name']), list(g.vs)))
name_to_id = {v: k for k, v in id_to_name.items()}

# add vertex id to pub_keys in cluster dataframe
clusters["vertex_id"] = clusters["pub_key"].apply(lambda x: name_to_id[x] if x in name_to_id else -1)
existing_clusters = clusters[clusters.vertex_id != -1]
existing_clusters = existing_clusters[existing_clusters.groupby("cluster")['cluster'].transform('size') > 1]

cluster_ids = existing_clusters.cluster.drop_duplicates().values.tolist()
cluster_to_node = { cluster_id: existing_clusters[existing_clusters.cluster == cluster_id]["vertex_id"].values.tolist() for cluster_id in cluster_ids}
node_to_cluster = {}
for k,v in cluster_to_node.items():
    for x in v:
        node_to_cluster.setdefault(x,k)


def computePrivacyStats(intermediaries, target, cluster_id):
    entity_vids = cluster_to_node[cluster_id]
    if(len(intermediaries) == 0):
        return {"wormhole":[],
                "wormhole_with_target":[],
                "any_wormhole":[],
                "value_privacy": [],
                "relationship_anonymity": []}
    else:
        # check if entity is intermediary
        entity_in_intermediaries_idx = sorted(map(intermediaries.index, set(intermediaries).intersection(entity_vids)))
        entityIsIntermediary = cluster_id if len(entity_in_intermediaries_idx) > 0 else []
        relationshipAnonymity = cluster_id if (intermediaries[0] in entity_vids) and (intermediaries[-1] in entity_vids) else []

        # check if wormhole attack is possible
        if((len(intermediaries) <= 1) | (not entityIsIntermediary)):
            hasWormhole = []
            hasWormholeWithTarget = []
        elif(len(intermediaries) <= 2):
            hasWormhole = []
            hasWormholeWithTarget = cluster_id if target in entity_vids and intermediaries[0] in entity_vids else []
        else: # intermediaries has length >= 3
            hasWormholeWithTarget = cluster_id if target in entity_vids and not set(intermediaries[0:-1]).isdisjoint(set(entity_vids)) else []
            hasWormhole = [] # default assumption

            entity_vids_idx = [intermediaries.index(x) for x in entity_vids if x in intermediaries]
            non_entity_idx = list(set(range(0, len(intermediaries))).difference(set(entity_vids_idx)))
            potentially_skipped_idx = [non_entity_id for non_entity_id in non_entity_idx if (non_entity_id > min(entity_vids_idx) and non_entity_id < max(entity_vids_idx))]
            potentially_skipped_idx
            for p_skipped in potentially_skipped_idx:
                for left in [i for i in entity_vids_idx if i < p_skipped]:
                    for right in [i for i in entity_vids_idx if i > p_skipped]:
                        hasWormhole = cluster_id

        return {"wormhole":hasWormhole,
                "wormhole_with_target":hasWormholeWithTarget,
                "any_wormhole": hasWormhole if hasWormhole else hasWormholeWithTarget,
                "value_privacy": cluster_id if entityIsIntermediary else [],
                "relationship_anonymity": relationshipAnonymity}

tqdm.pandas()

def computeEntitiesForPath(intermediaries, rowTarget):
    elist = [computePrivacyStats(intermediaries, rowTarget, cluster_id) for cluster_id in cluster_ids]
    dd = defaultdict(list)

    for d in elist: # you can list as many input dicts as you want here
        for key, value in d.items():
            if value != []:
                dd[key].append(value)
            else:
                dd.setdefault(key, [])
    return(dd)
myDF = pd.DataFrame(shortest_paths.progress_apply(lambda row: computeEntitiesForPath(row["intermediaries"], row["target"]), axis=1).tolist())

pathInfos = shortest_paths.merge(myDF, left_index=True, right_index=True)
pathInfos.to_pickle(outputFile)
