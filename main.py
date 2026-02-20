from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import traceback

from config import PORT, HOST
from bigquery_client import get_cached_schema, get_cached_products, run_query, refresh_caches
from gemini_client import generate_sql, generate_answer, generate_fallback_answer

app = FastAPI(title="Vendit Chatbot Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


class ChatResponse(BaseModel):
    answer: str
    sql: str | None = None
    data: list[dict] | None = None
    error: str | None = None


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    try:
        schema = get_cached_schema()
        products = get_cached_products()

        # Generate SQL from user question
        sql = generate_sql(req.message, schema, products, req.history)

        # If Gemini says it can't answer with SQL, use fallback
        if "unanswerable" in sql.lower() or not sql:
            answer = generate_fallback_answer(req.message, req.history)
            return ChatResponse(answer=answer)

        # Execute the SQL query on BigQuery
        try:
            results = run_query(sql)
        except Exception as e:
            error_msg = str(e)
            answer = generate_fallback_answer(
                f"The user asked: '{req.message}'. The generated SQL failed with: {error_msg}. "
                f"Please apologize and suggest how they might rephrase their question.",
                req.history,
            )
            return ChatResponse(answer=answer, sql=sql, error=error_msg)

        # Generate natural language answer from results
        answer = generate_answer(req.message, sql, results, req.history)

        return ChatResponse(answer=answer, sql=sql, data=results[:50])

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/refresh-schema")
async def refresh_schema():
    schema = refresh_caches()
    return {"status": "ok", "schema_preview": schema[:500]}


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
