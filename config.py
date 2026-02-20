import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
BIGQUERY_DATASET = os.getenv("BIGQUERY_DATASET", "salesData")
BIGQUERY_TABLE = os.getenv("BIGQUERY_TABLE", "totalsales")
BQ_LOCATION = os.getenv("BQ_LOCATION", "us-central1")
PORT = int(os.getenv("PORT", "8082"))
HOST = os.getenv("HOST", "0.0.0.0")
