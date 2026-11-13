import dlt
from pyspark.sql.functions import *


# STAGING TABLE 
@dlt.table(
    name = "scd_stg"
)
def scd1_stg():
  df = spark.readStream.table("databricksansh.bronze.source")
  return df


# CREATE AN EMPTY STREAMING TABLE 
dlt.create_streaming_table(
    name = "scd1_table"
)


dlt.create_auto_cdc_flow(
  target = "scd1_table",
  source = "scd_stg",
  keys = ["product_id"],
  sequence_by = col("processDate"),
  stored_as_scd_type = 1
)


# CREATE AN EMPTY STREAMING TABLE 
dlt.create_streaming_table(
    name = "scd3_table"
)


dlt.create_auto_cdc_flow(
  target = "scd3_table",
  source = "scd_stg",
  keys = ["product_id"],
  sequence_by = col("processDate"),
  stored_as_scd_type = 2,
  except_column_list= ['processDate']
)





