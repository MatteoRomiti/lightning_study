load_datasets <- function() {
  funding.addr_entities <<- read_csv(
    paste0(dataset.path, "funding_addresses_entities.csv")
  )
  
  funding.entity_relations <<- read_csv(
    paste0(dataset.path, "funding_entities_incoming_relations.csv")
  )
  
  funding.entity_stats <<- read_csv(
    paste0(dataset.path, "funding_entities_stats.csv")
  )
  
  settlement.addr_entities <<- read_csv(
    paste0(dataset.path, "settlement_addresses_entities.csv")
  )
  
  settlement.entity_relations <<- read_csv(
    paste0(dataset.path, "settlement_entities_outgoing_relations.csv")
  )
  
  settlement.entity_stats <<- read_csv(
    paste0(dataset.path, "settlement_entities_stats.csv")
  )  
}