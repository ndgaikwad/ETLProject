import dlt
from pyspark.sql.functions import * 


# CREATE STREAMING TABLE [USING AUTOLOADER]
@dlt.table(
    name = 'autovol_table'
)
def autovol_table():
    df = spark.readStream.format("cloudFiles")\
                .option("cloudFiles.format","csv")\
                .load("/Volumes/databricksansh/bronze/autovol/raw/")
    return df


# CREATING STREAMING TABLE 
@dlt.table(
    name = 'autovol_table_enr'
)
def autovol_table_enr():
    df = spark.read.table("autovol_table")
    df = df.withColumn("flag",lit("Yes"))

    return df




