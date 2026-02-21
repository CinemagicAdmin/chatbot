from pathlib import Path
from google.cloud import bigquery
from google.oauth2 import service_account
from config import GCP_PROJECT_ID, BIGQUERY_DATASET, BIGQUERY_TABLE, BIGQUERY_DELIVERY_TABLE, BQ_LOCATION
import os

_client: bigquery.Client | None = None

# Resolve credentials path relative to this file's directory
_CREDS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
if _CREDS_PATH:
    _CREDS_PATH = str(Path(__file__).parent / _CREDS_PATH)


def get_client() -> bigquery.Client:
    global _client
    if _client is None:
        if _CREDS_PATH and Path(_CREDS_PATH).exists():
            credentials = service_account.Credentials.from_service_account_file(_CREDS_PATH)
            _client = bigquery.Client(project=GCP_PROJECT_ID, credentials=credentials)
        else:
            _client = bigquery.Client(project=GCP_PROJECT_ID)
    return _client


def _fetch_table_schema(table_name: str) -> str:
    """Fetch schema for a given table."""
    client = get_client()
    table_ref = f"{GCP_PROJECT_ID}.{BIGQUERY_DATASET}.{table_name}"
    table = client.get_table(table_ref)
    columns = [f"{f.name} ({f.field_type})" for f in table.schema]
    return f"Table: {table_name}\nColumns: {', '.join(columns)}"


def get_table_schema() -> str:
    """Fetch schema for the totalsales table."""
    return _fetch_table_schema(BIGQUERY_TABLE)


def get_delivery_schema() -> str:
    """Fetch schema for the deliveryroutes table."""
    return _fetch_table_schema(BIGQUERY_DELIVERY_TABLE)


def get_known_products() -> list[str]:
    """Fetch distinct product names from the table."""
    client = get_client()
    table_ref = f"{GCP_PROJECT_ID}.{BIGQUERY_DATASET}.{BIGQUERY_TABLE}"
    try:
        query = f"SELECT DISTINCT name FROM `{table_ref}` WHERE name IS NOT NULL LIMIT 300"
        rows = client.query(query, location=BQ_LOCATION).result()
        return [row["name"] for row in rows]
    except Exception:
        return []


def run_query(sql: str) -> list[dict]:
    client = get_client()
    rows = client.query(sql, location=BQ_LOCATION).result()
    return [dict(row) for row in rows]


_schema_cache: str | None = None
_delivery_schema_cache: str | None = None
_products_cache: list[str] | None = None


def get_cached_schema() -> str:
    global _schema_cache
    if _schema_cache is None:
        _schema_cache = get_table_schema()
    return _schema_cache


def get_cached_delivery_schema() -> str:
    global _delivery_schema_cache
    if _delivery_schema_cache is None:
        _delivery_schema_cache = get_delivery_schema()
    return _delivery_schema_cache


def get_cached_products() -> list[str]:
    global _products_cache
    if _products_cache is None:
        _products_cache = get_known_products()
    return _products_cache


def refresh_caches():
    global _schema_cache, _delivery_schema_cache, _products_cache
    _schema_cache = None
    _delivery_schema_cache = None
    _products_cache = None
    return get_cached_schema()
