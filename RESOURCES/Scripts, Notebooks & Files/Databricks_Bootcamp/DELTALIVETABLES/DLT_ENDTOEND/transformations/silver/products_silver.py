import dlt 
from pyspark.sql.functions import * 

# STREAMING VIEW
@dlt.view(
    name = "products_silver_view"
)
def products_silver_view():
    df_prod = spark.readStream.table("products_bronze")
    df_prod = df_prod.withColumn("processDate",current_timestamp())
    return df_prod



# PRODUCTS SILVER TABLE (WITH UPSERT)
dlt.create_streaming_table(name = 'products_silver')

dlt.create_auto_cdc_flow(
    target = 'products_silver',
    source = 'products_silver_view',
    keys = ['product_id'],
    sequence_by = col('processDate'),
    stored_as_scd_type = 1
)






