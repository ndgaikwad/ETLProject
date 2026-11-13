import dlt

# CREATE AN EMPTY STREAMING TABLE 
dlt.create_streaming_table(
    name = 'append_table'
)


# CREATING FLOW 1 
@dlt.append_flow(
    target = 'append_table'
)
def flow_1():
    df = spark.readStream.format("cloudFiles")\
                .option("cloudFiles.format", "csv")\
                .load("/Volumes/databricksansh/bronze/autovol/flow1/")
    return df


# CREATING FLOW 2
@dlt.append_flow(
    target = 'append_table'
)
def flow_2():
    df = spark.readStream.format("cloudFiles")\
                .option("cloudFiles.format", "csv")\
                .load("/Volumes/databricksansh/bronze/autovol/flow2/")
    return df


