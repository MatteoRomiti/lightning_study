from matplotlib import rcParams
import pandas as pd
import numpy as np
from tqdm import tqdm  # progress bars
from ipaddress import IPv4Address, IPv4Network, IPv6Address, IPv6Network
from jellyfish import *  # edit distances
import pylcs  # longest common subsequence
import scipy.cluster.hierarchy
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.axis as ax
from plotnine import *
theme_publication = theme_bw() + theme(text=element_text(family="cmr10", size=12, color="black"),
                                       axis_title=element_text(size=14))

print("Attention: this script will run multiple hours!")
data_dir = "../data/joined/level_2/"
output_dir = "../data/joined/results/"


# Load aliases
alias_file = data_dir+"node.csv"

node_aliases = pd.read_csv(alias_file)
# have each pub_key / alias combination in a separate row
node_aliases.alias = node_aliases.alias.apply(lambda x: x.split("|"))
node_aliases = node_aliases.explode("alias")
# filter to remove empty aliases
node_aliases = node_aliases[node_aliases.alias.str.len() > 0].copy()
print("Got", len(node_aliases), "aliases")


# Load IP addresses
ip_address_file = data_dir+"ip_address.csv"

node_ips = pd.read_csv(ip_address_file)
# have each pub_key / ip combination in a separate row
node_ips.ip_address = node_ips.ip_address.apply(lambda x: x.split("|"))
node_ips = node_ips.explode("ip_address")
# separate port and ip address for easier querying
node_ips['port'] = node_ips.ip_address.apply(lambda x: x.rsplit(":", 1)[1])
node_ips['ip_address'] = node_ips.ip_address.apply(lambda x: x.rsplit(":", 1)[0].strip("[]"))

# FILTER (remove addresses that don't make sense)
# https://en.wikipedia.org/wiki/Reserved_IP_addresses


def is_reserved_address(ip_address):
    if ".onion" in ip_address:
        return(False)
    special_use_nets_ipv4 = ["0.0.0.0/8", "10.0.0.0/8", "100.64.0.0/10", "127.0.0.0/8", "169.254.0.0/16", "172.16.0.0/12", "192.0.0.0/24", "192.0.2.0/24",
                             "192.88.99.0/24", "192.168.0.0/16", "198.18.0.0/15", "198.51.100.0/24", "203.0.113.0/24", "224.0.0.0/4", "240.0.0.0/4", "255.255.255.255/32"]
    special_use_nets_ipv6 = ["::/0", "::/128", "::1/128", "::ffff:0:0/96", "::ffff:0:0:0/96", "64:ff9b::/96",
                             "100::/64", "2001::/32", "2001:20::/28", "2001:db8::/32", "2002::/16", "fc00::/7", "fe80::/10", "ff00::/8"]
    if(":" in ip_address):  # ipv6
        return(any([IPv6Address(ip_address) in IPv6Network(net) for net in special_use_nets_ipv6]))
    else:  # ipv4
        return(any([IPv4Address(ip_address) in IPv4Network(net) for net in special_use_nets_ipv4]))


reserved_ips = node_ips.ip_address.apply(is_reserved_address)
print("Removing a total of: ", sum(reserved_ips), "reserved IPs")
node_ips = node_ips[~reserved_ips]

try:
    whois_data = pd.read_csv(data_dir+"whois.csv")
    whois_data = whois_data[~whois_data.entities.isna()]
except:
    print("No existing whois data, querying all IP addresses now")
    from ipwhois import IPWhois

    def lookup(ip_address):
        fail = {"query": ip_address}
        if ".onion" in ip_address:
            return(fail)
        else:
            try:
                res = IPWhois(ip_address).lookup_rdap(depth=1)
                return(res)
            except:
                print(ip_address, "couldn't be queried...")
                return(fail)
    whois_jsons = [lookup(ip_address) for ip_address in tqdm(node_ips.ip_address.unique())]
    whois_data = pd.DataFrame.from_dict(whois_jsons)
    whois_data.to_csv(data_dir+"whois.csv", index=False)

# only keep asn and ip_address
whois_data = whois_data[["asn", "query"]].rename(columns={"query": "ip_address"})


def compute_distances(alias_df, distance_func):
    # https://codereview.stackexchange.com/questions/37026/string-matching-and-clustering
    # generate pairwise indices of the alias dataframe without duplication
    pairwise_indices = np.triu_indices(len(alias_df.alias), 1)

    def get_dist(coord):
        i, j = coord
        # compute distance with some distance metric
        return distance_func(alias_df.alias.iloc[i], alias_df.alias.iloc[j])

    # compute pairwise distances
    dists = np.apply_along_axis(get_dist, 0, pairwise_indices)

    return(dists)


def cluster(alias_df, distance_measure, max_distance_threshold, dists=None):
    if dists is None:
        dists = compute_distances(alias_df, distance_measure)
    # perform hierarchical clustering based on distances
    Z = scipy.cluster.hierarchy.linkage(dists, method="complete")
    # return clusters based on a threshold t
    clusters = scipy.cluster.hierarchy.fcluster(Z, t=max_distance_threshold, criterion="distance")
    # assign cluster ids to original alias df
    alias_df["cluster"] = clusters

    return(alias_df, Z)


# distance measures
def relative_lcs(A, B):
    return(1 - pylcs.lcs2(A, B) / max(len(A), len(B)))


def lcs_distance(A, B):
    lcs = pylcs.lcs2(A, B)
    if(lcs == 0):
        return(1)
    else:
        return(1 / lcs)


def relative_levenshtein(A, B):
    levdist = levenshtein_distance(A, B)
    return(levdist/max(len(A), len(B)))


def relative_damerau_levenshtein(A, B):
    dalevdist = damerau_levenshtein_distance(A, B)
    return(dalevdist/max(len(A), len(B)))


def relative_hamming(A, B):
    hammdist = hamming_distance(A, B)
    return(hammdist/max(len(A), len(B)))


def jaro_distance(A, B):
    return(1 - jaro_similarity(A, B))


def jaro_winkler_distance(A, B):
    return(1 - jaro_winkler_similarity(A, B))


tmp_aliases = node_aliases[node_aliases.alias.str.contains("LNBIG")]
# add random "Lightning" aliases
tmp_aliases = tmp_aliases.append(
    node_aliases[node_aliases.alias.str.contains("Lightning")].sample(10, random_state=7))
# add entirely random aliases
tmp_aliases = tmp_aliases.append(node_aliases.sample(
    10, random_state=7)).drop_duplicates().reset_index(drop=True)
distance_measure = relative_lcs
# the common substring needs to account for 70% of all letters of the longer string
max_distance_threshold = 1 - 0.7

distance_measure = relative_lcs  # jellyfish.levenshtein_distance
max_distance_threshold = 0.46

clusters, Z = cluster(tmp_aliases, distance_measure, max_distance_threshold)
# clusters


rcParams['font.family'] = 'cmr10'

# plot dendrogram (only makes sense for smaller data...)
fig = plt.figure(figsize=(9, 16))
ax = fig.add_subplot(1, 1, 1)
dn = scipy.cluster.hierarchy.dendrogram(
    Z, orientation="right", labels=clusters.alias.values, color_threshold=max_distance_threshold)
ax.axvline(x=max_distance_threshold, color='r', ls="--")
ax.xaxis.set_ticks_position("top")
plt.savefig("alias_dendrogram_example.pdf", papertype="letter", bbox_inches="tight")


def get_same_asn_clusters(cluster_df):
    clusters_with_asn = cluster_df.merge(node_ips, how="left").merge(whois_data, how="left")
    clusters_with_asn = clusters_with_asn.dropna()  # remove .onion and aliases without known IP
    same_asn_clusters = clusters_with_asn.groupby("cluster") \
        .filter(lambda x: (x["asn"].nunique() == 1) & (x["pub_key"].nunique() > 1)) \
        .sort_values("cluster")
    return(same_asn_clusters)


same_asn_clusters = get_same_asn_clusters(clusters)
same_asn_clusters.groupby(["cluster", "pub_key"])["alias"].agg(
    lambda x: '|'.join(set(x))).reset_index()


def evaluate_single_result(clustered_alias_df, Z=None):
    #clusters = get_same_asn_clusters(clustered_alias_df)
    clusters = get_same_asn_clusters(clustered_alias_df)[["pub_key", "cluster"]].drop_duplicates()

    node_count = len(clusters)
    cluster_count = len(clusters.groupby("cluster").filter(
        lambda x: len(x) > 1).groupby("cluster").count())
    cluster_count_min3 = len(clusters.groupby("cluster").filter(
        lambda x: len(x) > 2).groupby("cluster").count())
    cluster_count_min26 = len(clusters.groupby("cluster").filter(
        lambda x: len(x) >= 26).groupby("cluster").count())

    return(pd.Series({"node_count": node_count,
                      "cluster_count": cluster_count,
                      "cluster_count_min3": cluster_count_min3,
                      "cluster_count_min26": cluster_count_min26}))


def evaluate_measure(alias_df, dist_measure, thresholds):
    dists = compute_distances(alias_df, dist_measure)
    df = pd.DataFrame({"measure": dist_measure.__name__.replace("_", " "), "threshold": thresholds})
    stats = df.apply(lambda x:
                     evaluate_single_result(
                         *cluster(alias_df, dist_measure,
                                  x["threshold"], dists)),
                     axis=1)
    result = pd.concat([df, stats], axis=1)
    print("Finished", dist_measure.__name__)
    return(result)


evaluate_single_result(clusters)
tmp_aliases = node_aliases.copy()
results = pd.concat([
    evaluate_measure(tmp_aliases, relative_lcs, np.arange(0, 1, 0.01)),
    evaluate_measure(tmp_aliases, lcs_distance, 1/np.arange(1, 15, 1)),
    evaluate_measure(tmp_aliases, levenshtein_distance, np.arange(0, 10, 1)),
    evaluate_measure(tmp_aliases, relative_levenshtein, np.arange(0, 1, 0.01)),
    evaluate_measure(tmp_aliases, damerau_levenshtein_distance, np.arange(0, 10, 1)),
    evaluate_measure(tmp_aliases, relative_damerau_levenshtein, np.arange(0, 1, 0.01)),
    evaluate_measure(tmp_aliases, hamming_distance, np.arange(0, 10, 1)),
    evaluate_measure(tmp_aliases, relative_hamming, np.arange(0, 1, 0.01)),
    evaluate_measure(tmp_aliases, jaro_distance, np.arange(0, 1, 0.01)),
    evaluate_measure(tmp_aliases, jaro_winkler_distance, np.arange(0, 1, 0.01))
])

#results.to_csv("~/Desktop/results.csv", index=False)
results[results.cluster_count_min26 == 2].sort_values("node_count", ascending=False).dropna()


# plot method comparison

bestMeasure_for_plot = results[results.groupby(['measure'])['cluster_count_min26'].transform(
    max) == results['cluster_count_min26']].reset_index(drop=True)
bestMeasure_for_plot = bestMeasure_for_plot.iloc[bestMeasure_for_plot.reset_index().groupby(["measure"])[
    'node_count'].idxmax()]

bestMeasure_for_plot = bestMeasure_for_plot.sort_values("node_count", ascending=False)
measure_list = bestMeasure_for_plot['measure'].values.tolist()
measure_cat = pd.Categorical(bestMeasure_for_plot['measure'], categories=measure_list)
bestMeasure_for_plot = bestMeasure_for_plot.assign(measure_cat=measure_cat)
bestMeasure_for_plot["label_pos"] = bestMeasure_for_plot["node_count"]/2
bestMeasure_for_plot["label_text"] = bestMeasure_for_plot.apply(
    lambda x: str(x["cluster_count"]) + " clusters at threshold "+str(round(x['threshold'], 2)), axis=1)

plot = ggplot(bestMeasure_for_plot) +\
    geom_bar(aes(x="measure_cat", y="node_count"), stat="identity", colour="black", fill="white") +\
    geom_text(aes(x="measure_cat", y="label_pos", label="label_text"), angle=90, colour="black") +\
    labs(x="String distance measure", y="Total clustered lightning nodes") +\
    theme_publication +\
    theme(axis_text_x=element_text(rotation=45, vjust=1, hjust=1))

plot.save("alias_clustering_white.pdf", width=5, height=5)


# print summary of best method:
best = results[results.groupby(['measure'])['cluster_count_min26'].transform(
    max) == results['cluster_count_min26']].reset_index(drop=True)
best = best[best["node_count"] == best["node_count"].max()].iloc[0]
print(best)

print("Running final alias clustering with best configuration")
final_alias_cluster, _ = cluster(
    node_aliases, globals()[best.measure.replace(" ", "_")], best.threshold)
#final_alias_cluster, _ = cluster(node_aliases.head(1000), relative_lcs, 0.46)
alias_asn_clusters = get_same_asn_clusters(final_alias_cluster)[
    ["pub_key", "cluster"]].drop_duplicates()
alias_asn_clusters["cluster_origin"] = "alias/asn"

print("Clustering based on same IP/onion address")
same_ip_nodes = node_ips.drop(columns=['port']) \
    .groupby('ip_address') \
    .filter(lambda x: x['pub_key'].nunique() > 1) \
    .sort_values('ip_address')
same_ip_nodes = same_ip_nodes.rename(columns={"ip_address": "cluster"})
same_ip_nodes["cluster_origin"] = "address"
same_ip_nodes.head()

print("Merging both clusterings")
combined = pd.concat([alias_asn_clusters, same_ip_nodes])
G = nx.from_pandas_edgelist(combined, source="pub_key", target="cluster", create_using=nx.DiGraph)
l = list(nx.weakly_connected_components(G))
L = [dict.fromkeys(y, x) for x, y in enumerate(l)]
d = {k: v for d in L for k, v in d.items()}
mapping = pd.DataFrame(list(d.items()), columns=['pub_key', 'newcluster'])
mapping = mapping.merge(combined, how="left", on="pub_key").drop(columns="cluster").dropna()
mapping = mapping.groupby(["newcluster", "pub_key"])["cluster_origin"].agg(
    lambda x: ' & '.join(set(x))).reset_index()
mapping = mapping.merge(node_aliases, how="left")

final_clusters = mapping.groupby(["newcluster", "pub_key", "cluster_origin"])[
    "alias"].agg(lambda x: ' | '.join(set(x.dropna()))).reset_index()
final_clusters = final_clusters.rename(columns={"newcluster": "cluster"})
final_clusters.to_csv(output_dir + "alias_address_clusters.csv", index=False)

cluster_type_distribution = final_clusters.groupby("cluster_origin")["pub_key"].count()
print("Best clustering algorithm:\n", cluster_type_distribution)
print("Total nodes clustered: ", final_clusters["pub_key"].count())
print("Total cluster count:", final_clusters.cluster.nunique())
print("Largest clusters:")
final_clusters.groupby("cluster").agg(
    {"pub_key": len, "alias": lambda x: "{%s}" % ', '.join(x)}).sort_values("pub_key", ascending=False).head()
