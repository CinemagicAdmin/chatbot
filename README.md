# Vendit Chatbot Server

Analytics chatbot powered by **Gemini 2.5 Flash** + **BigQuery**. Answers natural language questions about your vending machine data.

## How it works

1. User asks a question in the Vendit Cloud chatbot UI
2. Server sends the question + BigQuery schema to Gemini to generate SQL
3. SQL runs against BigQuery
4. Results go back to Gemini to produce a human-readable answer
5. Answer returned to the frontend

## Setup

### 1. Install dependencies

```bash
cd "chatbot server"
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your values:

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Get from [Google AI Studio](https://aistudio.google.com/apikey) |
| `GCP_PROJECT_ID` | Your Google Cloud project ID |
| `BIGQUERY_DATASET` | The BigQuery dataset to query |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to GCP service account JSON (if not using `gcloud auth`) |

### 3. Authenticate with GCP

Either set `GOOGLE_APPLICATION_CREDENTIALS` in `.env` pointing to a service account JSON, or:

```bash
gcloud auth application-default login
```

The service account needs `BigQuery Data Viewer` and `BigQuery Job User` roles.

### 4. Run the server

```bash
python main.py
```

Server starts on `http://localhost:8081`.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/chat` | Send a message, get analytics answer |
| POST | `/refresh-schema` | Reload BigQuery table schemas |
| GET | `/health` | Health check |

### POST /chat

```json
// Request
{ "message": "What were total sales yesterday?", "history": [] }

// Response
{ "answer": "Yesterday's total sales were $1,234.56 across 89 transactions.", "sql": "SELECT ...", "data": [...] }
```

## Frontend

The Vendit Cloud frontend (`Chatbot.tsx`) is already wired to hit `localhost:8081/chat`. Set `VITE_API_BASE_URL=http://localhost:8081` in the Vendit Cloud `.env` if needed.
