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
        return jsonify({
            "error": True,
            "type": "missing_query",
            "message": "Missing 'query' in JSON body.",
            "sql": None
        }), 400

    # 1. Normalize query
    normalized_q = normalize_query(user_q)

    # 2. Build prompt & generate SQL
    prompt = build_prompt(SCHEMA, normalized_q)
    sql = generate_sql(prompt)

    # 3. Add LIMIT if missing
    if " limit " not in sql.lower():
        sql = f"{sql}\nLIMIT {DEFAULT_LIMIT}"

    # 4. Validate SQL safety
    safe, reason = is_safe_sql(sql)
    if not safe:
        return jsonify({
            "error": True,
            "type": "unsafe_sql",
            "message": f"Unsafe SQL: {reason}",
            "sql": sql
        }), 400

    # 5. Execute SQL
    try:
        rows = fetch_rows(sql)

        if not rows:  # No results
            return jsonify({
                "error": True,
                "type": "no_rows",
                "message": "No matching records found for your query.",
                "sql": sql
            }), 200

        # ✅ Success
        return jsonify({
            "error": False,
            "type": "success",
            "message": "Your result has been generated.",
            "rows": rows,
            "sql": sql
        }), 200

    except Exception as e:
        err_msg = str(e).lower()
        error_type = None
        friendly_message = None

        # Categorize known errors
        if "column" in err_msg and "does not exist" in err_msg:
            error_type = "missing_column"
            friendly_message = "One or more columns in your query do not exist in our database."
        elif "relation" in err_msg and "does not exist" in err_msg:
            error_type = "missing_table"
            friendly_message = "One or more tables in your query do not exist in our database."
        elif "operator does not exist" in err_msg or "invalid input syntax" in err_msg:
            error_type = "invalid_operator"
            friendly_message = "The query attempted an invalid comparison or data type operation."
        elif "statement timeout" in err_msg:
            error_type = "timeout"
            friendly_message = "The query took too long to run and was canceled."
        elif "could not connect" in err_msg or "connection refused" in err_msg:
            error_type = "connection_error"
            friendly_message = "Could not connect to the database. Please try again later."
        elif "syntax error" in err_msg:
            error_type = "syntax_error"
            friendly_message = "There was a syntax issue in generating the query."

        # Default unknown error
        if error_type is None:
            error_type = "unknown_error"
            friendly_message = "Seems like something went wrong in generating your result. Please try again."

        return jsonify({
            "error": True,
            "type": error_type,
            "message": friendly_message,
            "sql": sql
        }), 400

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)