import dlt 

# INGESTING SALES DATA 
@dlt.table(
    name = 'sales_bronze'
)
def sales_bronze():
    df = spark.readStream.format("cloudFiles")\
                .option("cloudFiles.format", "csv")\
                .load("/Volumes/databricksansh/bronze/bronze_volume/sales/")
    return df

# INGESTING STORES DATA 
@dlt.table(
    name = 'stores_bronze'
)
def stores_bronze():
    df = spark.readStream.format("cloudFiles")\
                .option("cloudFiles.format", "csv")\
                .load("/Volumes/databricksansh/bronze/bronze_volume/stores/")
    return df


# INGESTING PRODUCTS DATA 
@dlt.table(
    name = 'products_bronze'
)
def products_bronze():
    df = spark.readStream.format("cloudFiles")\
                .option("cloudFiles.format", "csv")\
                .load("/Volumes/databricksansh/bronze/bronze_volume/products/")
    return df


# INGESTING  DATA 
@dlt.table(
    name = 'customers_bronze'
)
def customers_bronze():
    df = spark.readStream.format("cloudFiles")\
                .option("cloudFiles.format", "csv")\
                .load("/Volumes/databricksansh/bronze/bronze_volume/customers/")
    return df

