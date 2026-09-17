import snowflake.connector
import pyodbc
import logging

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

BATCH_SIZE = 5000

SNOWFLAKE_CONFIG = {
    "user": "SNOWFLAKE_USER",
    "password": "SNOWFLAKE_PASSWORD",
    "account": "YOUR_ACCOUNT",
    "warehouse": "YOUR_WAREHOUSE",
    "database": "SOURCE_DB",
    "schema": "SOURCE_SCHEMA",
    "role": "YOUR_ROLE"
}

SQL_SERVER_CONNECTION = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=your_sql_server,1433;"
    "DATABASE=your_database;"
    "UID=your_user;"
    "PWD=your_password;"
    "Encrypt=no;"
    "TrustServerCertificate=yes;"
)

SNOWFLAKE_SELECT = """
SELECT
    CUSTOMER_ID,
    CUSTOMER_NAME,
    EMAIL,
    CREATED_DATE,
    AMOUNT
FROM SOURCE_DB.SOURCE_SCHEMA.CUSTOMER
"""

SQL_SERVER_INSERT = """
INSERT INTO dbo.RAW_CUSTOMER
(
    CUSTOMER_ID,
    CUSTOMER_NAME,
    EMAIL,
    CREATED_DATE,
    AMOUNT
)
VALUES (?, ?, ?, ?, ?)
"""


# ---------------------------------------------------------
# LOGGING
# ---------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


# ---------------------------------------------------------
# COPY FUNCTION
# ---------------------------------------------------------

def copy_snowflake_to_sqlserver():

    sf_conn = None
    sf_cursor = None
    sql_conn = None
    sql_cursor = None

    total_rows = 0

    try:
        # -------------------------------------------------
        # Connect to Snowflake
        # -------------------------------------------------

        logging.info("Connecting to Snowflake...")

        sf_conn = snowflake.connector.connect(
            **SNOWFLAKE_CONFIG
        )

        sf_cursor = sf_conn.cursor()

        logging.info("Executing Snowflake SELECT...")

        sf_cursor.execute(SNOWFLAKE_SELECT)

        # -------------------------------------------------
        # Connect to SQL Server
        # -------------------------------------------------

        logging.info("Connecting to SQL Server...")

        sql_conn = pyodbc.connect(
            SQL_SERVER_CONNECTION,
            autocommit=False
        )

        sql_cursor = sql_conn.cursor()

        # Important for bulk inserts
        sql_cursor.fast_executemany = True

        # -------------------------------------------------
        # Fetch and insert batches
        # -------------------------------------------------

        while True:

            rows = sf_cursor.fetchmany(BATCH_SIZE)

            if not rows:
                break

            sql_cursor.executemany(
                SQL_SERVER_INSERT,
                rows
            )

            sql_conn.commit()

            total_rows += len(rows)

            logging.info(
                "Inserted %s rows | Total = %s",
                len(rows),
                total_rows
            )

        logging.info(
            "Data copy completed successfully. Total rows = %s",
            total_rows
        )

    except Exception:
        logging.exception("Data copy failed.")

        if sql_conn:
            sql_conn.rollback()

        raise

    finally:

        if sf_cursor:
            sf_cursor.close()

        if sf_conn:
            sf_conn.close()

        if sql_cursor:
            sql_cursor.close()

        if sql_conn:
            sql_conn.close()

        logging.info("Connections closed.")


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

if __name__ == "__main__":
    copy_snowflake_to_sqlserver()