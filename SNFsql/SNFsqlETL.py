import sys
import uuid
import time
import logging
from datetime import datetime

import pyodbc
import snowflake.connector


# =========================================================
# CONFIGURATION
# =========================================================

BATCH_SIZE = 10_000
MAX_RETRIES = 3

SNOWFLAKE_CONFIG = {
    "user": "SF_USER",
    "password": "SF_PASSWORD",
    "account": "SF_ACCOUNT",
    "warehouse": "ETL_WH",
    "database": "SOURCE_DB",
    "schema": "SOURCE_SCHEMA",
    "role": "ETL_ROLE"
}

SQLSERVER_CONNECTION = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=SQLSERVERNAME,1433;"
    "DATABASE=EDW;"
    "UID=etl_user;"
    "PWD=your_password;"
    "Encrypt=no;"
    "TrustServerCertificate=yes;"
)


SF_SQL = """
SELECT
    CUSTOMER_ID,
    CUSTOMER_NAME,
    EMAIL,
    CREATED_DATE,
    AMOUNT
FROM SOURCE_DB.SOURCE_SCHEMA.CUSTOMER
"""


INSERT_SQL = """
INSERT INTO dbo.RAW_CUSTOMER_STG
(
    CUSTOMER_ID,
    CUSTOMER_NAME,
    EMAIL,
    CREATED_DATE,
    AMOUNT,
    ETL_BATCH_ID,
    ETL_LOAD_DTM
)
VALUES (?, ?, ?, ?, ?, ?, ?)
"""


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("etl.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


# =========================================================
# CONNECTIONS
# =========================================================

def get_snowflake_connection():
    return snowflake.connector.connect(**SNOWFLAKE_CONFIG)


def get_sqlserver_connection():
    return pyodbc.connect(
        SQLSERVER_CONNECTION,
        autocommit=False
    )


# =========================================================
# ETL AUDIT
# =========================================================

def start_batch(conn, batch_id):

    sql = """
    INSERT INTO dbo.ETL_BATCH_LOG
    (
        BATCH_ID,
        PROCESS_NAME,
        START_TIME,
        STATUS
    )
    VALUES (?, ?, ?, ?)
    """

    cursor = conn.cursor()

    cursor.execute(
        sql,
        batch_id,
        "SNOWFLAKE_TO_RAW_CUSTOMER",
        datetime.now(),
        "RUNNING"
    )

    conn.commit()


def complete_batch(
    conn,
    batch_id,
    extracted,
    loaded
):

    sql = """
    UPDATE dbo.ETL_BATCH_LOG
    SET
        END_TIME = ?,
        SOURCE_ROW_COUNT = ?,
        TARGET_ROW_COUNT = ?,
        STATUS = 'SUCCESS'
    WHERE BATCH_ID = ?
    """

    cursor = conn.cursor()

    cursor.execute(
        sql,
        datetime.now(),
        extracted,
        loaded,
        batch_id
    )

    conn.commit()


def fail_batch(conn, batch_id, error_message):

    sql = """
    UPDATE dbo.ETL_BATCH_LOG
    SET
        END_TIME = ?,
        STATUS = 'FAILED',
        ERROR_MESSAGE = ?
    WHERE BATCH_ID = ?
    """

    cursor = conn.cursor()

    cursor.execute(
        sql,
        datetime.now(),
        str(error_message)[:4000],
        batch_id
    )

    conn.commit()


# =========================================================
# DATA LOAD
# =========================================================

def load_data(sf_conn, sql_conn, batch_id):

    sf_cursor = sf_conn.cursor()
    sql_cursor = sql_conn.cursor()

    sql_cursor.fast_executemany = True

    logger.info("Executing Snowflake query")

    sf_cursor.execute(SF_SQL)

    extracted_rows = 0
    loaded_rows = 0

    while True:

        rows = sf_cursor.fetchmany(BATCH_SIZE)

        if not rows:
            break

        extracted_rows += len(rows)

        load_time = datetime.now()

        # Add ETL metadata
        insert_rows = [
            tuple(row) + (batch_id, load_time)
            for row in rows
        ]

        retry = 0

        while True:

            try:

                sql_cursor.executemany(
                    INSERT_SQL,
                    insert_rows
                )

                sql_conn.commit()

                loaded_rows += len(insert_rows)

                logger.info(
                    "Batch loaded=%s | Total=%s",
                    len(insert_rows),
                    loaded_rows
                )

                break

            except Exception as exc:

                sql_conn.rollback()

                retry += 1

                logger.exception(
                    "Batch insert failed. Attempt %s/%s",
                    retry,
                    MAX_RETRIES
                )

                if retry >= MAX_RETRIES:
                    raise

                time.sleep(5 * retry)

    return extracted_rows, loaded_rows


# =========================================================
# VALIDATION
# =========================================================

def validate_load(conn, batch_id, expected_count):

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM dbo.RAW_CUSTOMER_STG
        WHERE ETL_BATCH_ID = ?
        """,
        batch_id
    )

    target_count = cursor.fetchone()[0]

    logger.info(
        "Validation source=%s target=%s",
        expected_count,
        target_count
    )

    if target_count != expected_count:

        raise ValueError(
            f"Row count mismatch. "
            f"Source={expected_count}, "
            f"Target={target_count}"
        )

    return target_count


# =========================================================
# PUBLISH
# =========================================================

def publish_data(conn, batch_id):

    cursor = conn.cursor()

    logger.info("Publishing staging data")

    try:

        # Transaction protects the live RAW table
        cursor.execute(
            "TRUNCATE TABLE dbo.RAW_CUSTOMER"
        )

        cursor.execute(
            """
            INSERT INTO dbo.RAW_CUSTOMER
            (
                CUSTOMER_ID,
                CUSTOMER_NAME,
                EMAIL,
                CREATED_DATE,
                AMOUNT,
                ETL_BATCH_ID,
                ETL_LOAD_DTM
            )
            SELECT
                CUSTOMER_ID,
                CUSTOMER_NAME,
                EMAIL,
                CREATED_DATE,
                AMOUNT,
                ETL_BATCH_ID,
                ETL_LOAD_DTM
            FROM dbo.RAW_CUSTOMER_STG
            WHERE ETL_BATCH_ID = ?
            """,
            batch_id
        )

        conn.commit()

    except Exception:

        conn.rollback()
        raise


# =========================================================
# MAIN ETL
# =========================================================

def run_etl():

    batch_id = str(uuid.uuid4())

    sf_conn = None
    sql_conn = None

    logger.info("=" * 70)
    logger.info("ETL started")
    logger.info("Batch ID: %s", batch_id)

    try:

        sql_conn = get_sqlserver_connection()

        start_batch(
            sql_conn,
            batch_id
        )

        # Clean staging
        cursor = sql_conn.cursor()

        cursor.execute(
            "TRUNCATE TABLE dbo.RAW_CUSTOMER_STG"
        )

        sql_conn.commit()

        # Snowflake connection
        sf_conn = get_snowflake_connection()

        # Extract + Load
        extracted, loaded = load_data(
            sf_conn,
            sql_conn,
            batch_id
        )

        # Validation
        target_count = validate_load(
            sql_conn,
            batch_id,
            extracted
        )

        # Publish
        publish_data(
            sql_conn,
            batch_id
        )

        # Audit success
        complete_batch(
            sql_conn,
            batch_id,
            extracted,
            target_count
        )

        logger.info(
            "ETL completed successfully. Rows=%s",
            target_count
        )

        # SQL Agent sees success
        sys.exit(0)

    except Exception as exc:

        logger.exception("ETL FAILED")

        if sql_conn:

            try:
                fail_batch(
                    sql_conn,
                    batch_id,
                    exc
                )
            except Exception:
                logger.exception(
                    "Unable to update audit table"
                )

        # SQL Agent sees failure
        sys.exit(1)

    finally:

        if sf_conn:
            sf_conn.close()

        if sql_conn:
            sql_conn.close()


if __name__ == "__main__":
    run_etl()