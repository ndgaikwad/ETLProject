from pyspark import pipelines as dp

@dp.table
def simple_table():
    return spark.range(10)