from google.cloud import bigquery
from google.oauth2 import service_account
from config import GCP_PROJECT_ID, BIGQUERY_DATASET, BIGQUERY_TABLE, BQ_LOCATION
import os

_client: bigquery.Client | None = None


def get_client() -> bigquery.Client:
    global _client
    if _client is None:
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if creds_path:
            credentials = service_account.Credentials.from_service_account_file(creds_path)
            _client = bigquery.Client(project=GCP_PROJECT_ID, credentials=credentials)
        else:
            _client = bigquery.Client(project=GCP_PROJECT_ID)
    return _client


def get_table_schema() -> str:
    """Fetch schema for the totalsales table."""
    client = get_client()
    table_ref = f"{GCP_PROJECT_ID}.{BIGQUERY_DATASET}.{BIGQUERY_TABLE}"
    table = client.get_table(table_ref)
    columns = [f"{f.name} ({f.field_type})" for f in table.schema]
    return f"Table: {BIGQUERY_TABLE}\nColumns: {', '.join(columns)}"


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
_products_cache: list[str] | None = None


def get_cached_schema() -> str:
    global _schema_cache
    if _schema_cache is None:
        _schema_cache = get_table_schema()
    return _schema_cache


def get_cached_products() -> list[str]:
    global _products_cache
    if _products_cache is None:
        _products_cache = get_known_products()
    return _products_cache


def refresh_caches():
    global _schema_cache, _products_cache
    _schema_cache = None
    _products_cache = None
    return get_cached_schema()
