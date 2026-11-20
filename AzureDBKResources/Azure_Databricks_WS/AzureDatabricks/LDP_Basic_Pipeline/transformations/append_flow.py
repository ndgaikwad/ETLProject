from pyspark import pipelines as dp
from pyspark.sql.functions import *


source_param = spark.conf.get("source_table")


@dp.table
def source_a_tbl():

    df = spark.readStream.table(source_param)
    return df 


@dp.table
def source_b_tbl():

    df = spark.readStream.table("azuredatabricks_catalog.ldp_basics.source_b")
    return df 


# Destination
dp.create_sink(
    "ext_datalake",
    "delta",
    {"path":"abfss://raw@azuredatabricksansh.dfs.core.windows.net/sinks"}
)


# Append Flow
@dp.append_flow(
    target="ext_datalake"
)
def append_source_a():
    df = spark.readStream.table("source_a_tbl")
    return df

@dp.append_flow(
    target="ext_datalake"
)
def append_source_b():
    df = spark.readStream.table("source_b_tbl")
    return df




