import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv

from db import fetch_rows, fetch_schema_tables_and_columns
from prompt_builder import build_prompt
from gemini_client import generate_sql
from sql_validator import is_safe_sql
from normalizer import normalize_query

load_dotenv()

DEFAULT_LIMIT = 500

app = Flask(__name__)

# Fetch schema once at startup (you can add a /schema-refresh endpoint later)
SCHEMA = fetch_schema_tables_and_columns()


@app.get("/health")
def health():
    return {"ok": True, "schema_tables": list(SCHEMA.keys())}


@app.post("/nlp-query")
def nlp_query():
    payload = request.get_json(force=True, silent=True) or {}
    user_q = payload.get("query", "").strip()
    if not user_q:
        return jsonify({"error": "Missing 'query' in JSON body"}), 400

    # 1. Normalize fuzzy keywords first
    normalized_q = normalize_query(user_q)

    # 2. Build prompt using normalized query
    prompt = build_prompt(SCHEMA, normalized_q)
    sql = generate_sql(prompt)

    # 3. Enforce LIMIT if missing (case-insensitive)
    if " limit " not in sql.lower():
        sql = f"{sql}\nLIMIT {DEFAULT_LIMIT}"

    # 4. Validate SQL
    safe, reason = is_safe_sql(sql)
    if not safe:
        return jsonify({"error": "unsafe_sql", "reason": reason, "sql": sql}), 400

    # 5. Execute SQL
    try:
        rows = fetch_rows(sql)
        return jsonify({"sql": sql, "rows": rows})
    except Exception as e:
        return jsonify({"error": "execution_error", "message": str(e), "sql": sql}), 400


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)