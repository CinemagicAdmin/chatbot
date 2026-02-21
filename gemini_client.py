import json
import re
from datetime import datetime, timezone, timedelta

import google.generativeai as genai
from config import GEMINI_API_KEY, GCP_PROJECT_ID, BIGQUERY_DATASET, BIGQUERY_TABLE, BIGQUERY_DELIVERY_TABLE

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")

FULL_TABLE = f"`{GCP_PROJECT_ID}.{BIGQUERY_DATASET}.{BIGQUERY_TABLE}`"
DELIVERY_TABLE = f"`{GCP_PROJECT_ID}.{BIGQUERY_DATASET}.{BIGQUERY_DELIVERY_TABLE}`"
KUWAIT_TZ = timezone(timedelta(hours=3))


def _get_kuwait_time() -> str:
    now = datetime.now(KUWAIT_TZ)
    return now.strftime("%Y-%m-%d %H:%M:%S")


def generate_sql(user_question: str, schema: str, delivery_schema: str, products: list[str], chat_history: list[dict]) -> str:
    products_ctx = f"Known products in database: {', '.join(products)}" if products else ""
    time_ctx = f"Current Date/Time in Kuwait (Asia/Kuwait, UTC+3): {_get_kuwait_time()}"

    history_ctx = "\n".join(
        f"{h['role']}: {h['content']}" for h in (chat_history or [])[-6:]
    )

    prompt = f"""You are a BigQuery SQL expert. Convert the user's natural language question into a standard SQL query.

Dataset Context:
Project ID: {GCP_PROJECT_ID}
Dataset ID: {BIGQUERY_DATASET}

Available Tables:

1. Sales Table (for sales, revenue, transactions, product data):
{schema}

2. Delivery Routes Table (for machine refills, delivery schedules, restocking):
{delivery_schema}

{products_ctx}
{time_ctx}

Conversation History:
{history_ctx}

Few-Shot Examples:
1. User: "What were the total sales yesterday?"
   Assistant: SELECT SUM(total_price) FROM {FULL_TABLE} WHERE EXTRACT(DATE FROM sold_at AT TIME ZONE 'Asia/Kuwait') = DATE_SUB(CURRENT_DATE('Asia/Kuwait'), INTERVAL 1 DAY)

2. User: "Which machine_name sold the most yesterday?"
   Assistant: SELECT machine_name, SUM(total_price) as total FROM {FULL_TABLE} WHERE EXTRACT(DATE FROM sold_at AT TIME ZONE 'Asia/Kuwait') = DATE_SUB(CURRENT_DATE('Asia/Kuwait'), INTERVAL 1 DAY) GROUP BY machine_name ORDER BY total DESC LIMIT 1

3. User: "When was machine X last refilled?"
   Assistant: SELECT machine_name, route_date FROM {DELIVERY_TABLE} WHERE machine_name = 'X' ORDER BY route_date DESC LIMIT 1

Rules:
- Return all price, amount, and revenue related values in KWD (Kuwaiti Dinar).
- Use the provided Current Date/Time in Kuwait for relative date queries.
- Return ONLY the SQL query. No markdown, no backticks, no explanation.
- For sales/revenue/product questions, query {FULL_TABLE}.
- For refill/delivery/restocking questions, query {DELIVERY_TABLE}.
- IMPORTANT: Always use machine_name (not machine_id) when selecting or displaying machine data. Users refer to machines by their machine_name, never by ID.
- When grouping by machine, always GROUP BY machine_name.
- IMPORTANT: Today's sales data is NOT available yet. If the user asks about "today" sales, return "no_today_data".
- If the question cannot be answered with the schema, return "unanswerable".

User Question: "{user_question}"
"""

    response = model.generate_content(prompt)
    sql = response.text.strip()
    sql = re.sub(r"^```(?:sql)?\s*", "", sql)
    sql = re.sub(r"\s*```$", "", sql)
    return sql


def generate_answer(user_question: str, sql: str, query_results: list[dict], chat_history: list[dict]) -> str:
    results_str = json.dumps(query_results[:50], default=str)

    prompt = f"""You are Vendit Assistant — a friendly colleague who helps with vending machine business analytics.

Talk naturally like a real person having a conversation. Be warm, direct, and helpful — not robotic.

User Question: "{user_question}"
SQL Query: {sql}
Raw Data: {results_str}

Rules:
- Talk like a human, not a report. Use casual but professional language.
  Good: "Yesterday you guys did 245 KWD in sales — pretty solid day!"
  Bad: "The total sales for the previous day amounted to 245.00 KWD."
- ALWAYS refer to machines by their machine_name, never by ID numbers.
  Good: "The Al Salmiya machine is your top performer"
  Bad: "Machine ID 47 has the highest sales"
- Use KWD for all financial amounts.
- If there's an interesting insight or trend, mention it naturally.
- Keep it conversational and concise — no bullet points or tables unless the data really needs it.
- If results are empty, just say so casually and suggest what they could ask instead.
- Don't mention SQL or technical details."""

    response = model.generate_content(prompt)
    return response.text.strip()


def generate_fallback_answer(user_question: str, chat_history: list[dict]) -> str:
    prompt = f"""You are Vendit Assistant — a friendly colleague who helps with vending machine business analytics.

Talk like a real person. Be warm and casual but professional.

You can help with:
- Sales numbers (revenue, transactions, daily/weekly/monthly trends)
- Machine performance (which machine_names are doing well, which need attention)
- Product insights (best sellers, what's moving where)
- Delivery routes and machine refills (when machines were restocked, delivery schedules)

If someone says hi, just be friendly and let them know what you can help with. Keep it short and natural.

User: {user_question}"""

    response = model.generate_content(prompt)
    return response.text.strip()
