import dlt 
from pyspark.sql.functions import * 

# STREAMING VIEW
@dlt.view(
    name = "customers_silver_view"
)
def customers_silver_view():
    df_cust = spark.readStream.table("customers_bronze")
    df_cust = df_cust.withColumn("name",upper(col("name")))
    df_cust = df_cust.withColumn("domain",split(col("email"),"@")[1])
    df_cust = df_cust.withColumn("processDate",current_timestamp())
    return df_cust



# CUSTOMERS SILVER TABLE (WITH UPSERT)
dlt.create_streaming_table(name = 'customers_silver')

dlt.create_auto_cdc_flow(
    target = 'customers_silver',
    source = 'customers_silver_view',
    keys = ['customer_id'],
    sequence_by = col('processDate'),
    stored_as_scd_type = 1
)






