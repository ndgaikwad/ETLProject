from pyspark import pipelines as dp
from pyspark.sql.functions import *


@dp.table
def gold_obt_test_final():

    trips = (
        spark.readStream.table("silver_trips_final")
        .withWatermark("updated_datetime", "10 minutes")
        .alias("t")
    )

    customers = (
        spark.read.table("azuredatabricks_catalog.medallion.customers")
        .alias("c")
    )

    vehicles = (
        spark.read.table("azuredatabricks_catalog.medallion.vehicles")
        .alias("v")
    )

    payments = (
        spark.read.table("azuredatabricks_catalog.medallion.payments")
        .alias("p")
    )

    drivers = (
        spark.read.table("azuredatabricks_catalog.medallion.drivers")
        .alias("d")
    )


    df_join = (
        trips
        .join(
            customers,
            col("c.customer_id") == col("t.customer_id"),
            "left"
        )
        .join(
            drivers,
            col("t.driver_id") == col("d.driver_id"),
            "left"
        )
        .join(
            vehicles,
            col("d.driver_id") == col("v.driver_id"),
            "left"
        )
        .join(
            payments,
            col("t.trip_id") == col("p.trip_id"),
            "left"
        )
    )


    df_join = df_join.select(

        # Trip
        col("t.trip_id"),
        col("t.pickup_datetime"),
        col("t.dropoff_datetime"),
        col("t.pickup_location"),
        col("t.dropoff_location"),
        col("t.distance_km"),
        col("t.fare_amount"),
        col("t.trip_status"),
        col("t.updated_datetime").alias("trip_updated_datetime"),


        # Customer
        col("t.customer_id"),
        col("c.customer_name"),
        col("c.email"),
        col("c.phone"),
        col("c.city").alias("customer_city"),
        col("c.rating").alias("customer_rating"),
        col("c.updated_datetime").alias("customer_updated_datetime"),


        # Driver
        col("t.driver_id"),
        col("d.driver_name"),
        col("d.license_number"),
        col("d.driver_rating"),
        col("d.city").alias("driver_city"),
        col("d.updated_datetime").alias("driver_updated_datetime"),


        # Vehicle
        col("v.vehicle_id"),
        col("v.vehicle_model"),
        col("v.vehicle_year"),
        col("v.license_plate"),
        col("v.updated_datetime").alias("vehicle_updated_datetime"),


        # Payment
        col("p.payment_id"),
        col("p.payment_method"),
        col("p.payment_amount"),
        col("p.payment_status"),
        col("p.updated_datetime").alias("payment_updated_datetime")
    )

    df_join = df_join.withColumn("gold_obt_processed_at", current_timestamp())

    return df_join


# Creating Customer Dimension

dp.create_streaming_live_table(
    name="dim_customers_final"
)

@dp.temporary_view
def stg_dim_customers_final():
    return (
        spark.readStream.table("gold_obt_test_final")
        .select(
            col("customer_id"),
            col("customer_name"),
            col("email"),
            col("phone"),
            col("customer_city"),
            col("customer_rating"),
            col("customer_updated_datetime"),
            col("gold_obt_processed_at").alias("dim_customer_processed_at")
        )  
    )


dp.create_auto_cdc_flow(
    source="stg_dim_customers_final",
    target="dim_customers_final",
    keys = ["customer_id"],
    stored_as_scd_type='2',
    sequence_by = "customer_updated_datetime",
)



