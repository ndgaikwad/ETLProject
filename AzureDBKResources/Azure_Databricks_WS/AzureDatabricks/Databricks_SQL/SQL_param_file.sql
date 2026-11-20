SELECT * FROM azuredatabricks_catalog.ldp_medallion.dim_customers
WHERE customer_city = :customer_city_param