from pyspark import pipelines as dp
from pyspark.sql.functions import *

@dp.table
def silver_trips_final():

    df = spark.readStream.format("cloudFiles") \
        .option("cloudFiles.format", "csv") \
        .option("cloudFiles.inferColumnTypes", "true") \
        .option("header", "true") \
        .load("abfss://raw@azuredatabricksansh.dfs.core.windows.net/tets/")

    return df




