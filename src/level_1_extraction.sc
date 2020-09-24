import com.datastax.spark.connector._

def loadTable(keyspace: String, table: String) = {
  spark.read.format("org.apache.spark.sql.cassandra")
    .options(Map("keyspace" -> keyspace, "table" -> table))
    .load
}

val keyspace = "btc_transformed_20200909"
val hdfsPath = "hdfs://spark-master/user/graphsense/LND"

val fundingAddr = sc.textFile(f"$hdfsPath%s/funding_addresses.csv").toDF("address")
val settlementAddr = sc.textFile(f"$hdfsPath/settlement_addresses.csv").toDF("address")

val addressId = loadTable(keyspace, "address_by_id_group")
val addressCluster = loadTable(keyspace, "address_cluster")
val clusterStats = loadTable(keyspace, "cluster")
val clusterTags = loadTable(keyspace, "cluster_tags")
val clusterIncomingRelations = loadTable(keyspace, "cluster_incoming_relations")
val clusterOutgoingRelations = loadTable(keyspace, "cluster_outgoing_relations")

val fundingAddrEntities = (fundingAddr
  .join(addressId.drop("address_id_group"), Seq("address"), "left")
  .join(addressCluster, Seq("address_id"), "left")
  .withColumnRenamed("cluster", "funding_entity")
  .withColumnRenamed("address", "funding_address")
  .select($"funding_address", $"funding_entity")
  .persist)
val settlementAddrEntities = (settlementAddr
  .join(addressId.drop("address_id_group"), Seq("address"), "left")
  .join(addressCluster, Seq("address_id"), "left")
  .withColumnRenamed("cluster", "settlement_entity")
  .withColumnRenamed("address", "settlement_address")
  .select($"settlement_address", $"settlement_entity")
  .persist)

val fundingEntitiesIncomingRelations = (fundingAddrEntities
  .join(
    clusterIncomingRelations.withColumnRenamed("dst_cluster", "funding_entity"),
    Seq("funding_entity"),
    "inner")
  .select(
    $"src_cluster".as("src_entity"),
    $"funding_entity",
    $"no_transactions",
    $"value.value")
  .distinct
  .persist)
val settlementEntitiesOutgoingRelations = (settlementAddrEntities
  .join(
    clusterOutgoingRelations.withColumnRenamed("src_cluster", "settlement_entity"),
    Seq("settlement_entity"),
    "inner")
  .select(
    $"settlement_entity",
    $"dst_cluster".as("dst_entity"),
    $"no_transactions",
    $"value.value")
  .distinct
  .persist)

val fundingEntitiesStats = (fundingAddrEntities
  .select($"funding_entity".as("entity"))
  .union(fundingEntitiesIncomingRelations.select($"src_entity".as("entity")))
  .distinct
  .join(
    clusterStats.withColumnRenamed("cluster", "entity"),
    Seq("entity"),
    "inner")
  .join(addressId.select($"address_id".as("entity"), $"address".as("repr_address")),
        Seq("entity"), "left")
  .select(
    $"entity",
    $"repr_address",
    $"no_addresses",
    $"no_incoming_txs",
    $"no_outgoing_txs",
    $"first_tx.timestamp".as("first_tx"),
    $"last_tx.timestamp".as("last_tx"),
    $"total_received.value".as("total_received"),
    $"total_spent.value".as("total_spent"),
    $"in_degree",
    $"out_degree"
  )
)

val settlementEntitiesStats = (settlementAddrEntities
  .select($"settlement_entity".as("entity"))
  .union(settlementEntitiesOutgoingRelations.select($"dst_entity".as("entity")))
  .distinct
  .join(
    clusterStats.withColumnRenamed("cluster", "entity"),
    Seq("entity"),
    "inner")
  .join(addressId.select($"address_id".as("entity"), $"address".as("repr_address")),
        Seq("entity"), "left")
  .select(
    $"entity",
    $"repr_address",
    $"no_addresses",
    $"no_incoming_txs",
    $"no_outgoing_txs",
    $"first_tx.timestamp".as("first_tx"),
    $"last_tx.timestamp".as("last_tx"),
    $"total_received.value".as("total_received"),
    $"total_spent.value".as("total_spent"),
    $"in_degree",
    $"out_degree"
  )
)

val fundingEntitiesIncomingTags = (fundingEntitiesIncomingRelations
  .select("src_entity")
  .join(clusterTags.withColumnRenamed("cluster", "src_entity"), Seq("src_entity"), "inner")
  .drop("cluster_group"))

val settlementEntitiesOutgoingTags = (settlementEntitiesOutgoingRelations
  .select("dst_entity")
  .join(clusterTags.withColumnRenamed("cluster", "dst_entity"), Seq("dst_entity"), "inner")
  .drop("cluster_group"))


(fundingAddrEntities
  .write.mode("overwrite")
  .parquet(f"$hdfsPath%s/funding_addresses_entities.parquet"))
(settlementAddrEntities
  .write.mode("overwrite")
  .parquet(f"$hdfsPath%s/settlement_addresses_entities.parquet"))

(fundingEntitiesIncomingRelations
  .write.mode("overwrite")
  .parquet(f"$hdfsPath%s/funding_entities_incoming_relations.parquet"))
(settlementEntitiesOutgoingRelations
  .write.mode("overwrite")
  .parquet(f"$hdfsPath%s/settlement_entities_outgoing_relations.parquet"))

(fundingEntitiesIncomingTags
  .write.mode("overwrite")
  .parquet(f"$hdfsPath%s/funding_entities_incoming_tags.parquet"))

(settlementEntitiesOutgoingTags
  .write.mode("overwrite")
  .parquet(f"$hdfsPath%s/settlement_entities_outgoing_tags.parquet"))

(fundingEntitiesStats
  .write.mode("overwrite")
  .parquet(f"$hdfsPath%s/funding_entities_stats.parquet"))

(settlementEntitiesStats
  .write.mode("overwrite")
  .parquet(f"$hdfsPath%s/settlement_entities_stats.parquet"))
