import pandas as pd

def make_cluster_aliases(nodeClustering):

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
        aliases = [item for sublist in [alias.split(" | ") for alias in aliases] for item in sublist]
        aliases = sorted(aliases, reverse=True) # avoid numeric strings in the beginnin
        mylcs = aliases[0]
        aliases = aliases[1:]
        before = ""
        after = ""
        while(len(aliases) > 0):
            try:
                newlcs = list(lcs(mylcs, aliases[0]))[0]
                if(len(newlcs) >= 3):
                    mylcs = newlcs
                index = aliases[0].index(mylcs)
                if(index > 0):
                    before = "*"
                if(len(aliases[0]) > (index + len(mylcs))):
                    after = "*"
                aliases = aliases[1:]
            except:
                after = after + ", ..."
                break#pass#return(before+mylcs+after) # if not all words share a common prefix
        mylcs = mylcs.encode('ascii', 'ignore').decode('ascii')
        if(len(mylcs) > 15):
            return(before+mylcs[0:15]+"...")
        else:
            return(before+mylcs+after)


    entities = nodeClustering.groupby("cluster").agg(
        {"pub_key":len, "alias": lambda x: multilcs(x)}
    ).reset_index().sort_values("pub_key", ascending=False)
    entities = entities.rename(columns={"pub_key":"cluster_size"}).reset_index(drop=True)
    return(entities)
