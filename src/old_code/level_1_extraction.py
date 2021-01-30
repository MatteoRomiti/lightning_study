#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pathlib
import pyarrow as pa

HOST = "spark-master"
USER = "graphsense"

hdfs = pa.hdfs.connect(host=HOST, port=8020, user=USER)
filenames = hdfs.ls(f"hdfs://{HOST}/user/{USER}/LND")

p = pathlib.Path("result/")
p.mkdir(parents=True, exist_ok=True)

for elem in filenames:
    if elem.endswith(".parquet"):
        basename = pathlib.Path(elem).stem
        print(f"Processing {basename}")
        tmp = hdfs.read_parquet(elem).to_pandas()
        tmp.to_csv(p / (basename + ".csv"), index=False)
