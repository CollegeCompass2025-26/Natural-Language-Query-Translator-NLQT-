import os
import time
import psutil
from flask import Flask, request, jsonify, render_template, g
from dotenv import load_dotenv
from db import fetch_rows, fetch_schema_tables_and_columns
from prompt_builder import build_prompt
from gemini_client import generate_sql
from sql_validator import is_safe_sql
from normalizer import normalize_query
from waitress import serve  # <-- Waitress import

load_dotenv()

DEFAULT_LIMIT = 500

app = Flask(__name__, static_folder="static", template_folder="templates")

# Fetch schema once at startup
SCHEMA = fetch_schema_tables_and_columns()

# ---------- MEMORY & REQUEST MONITOR ----------
@app.before_request
def start_timer():
    g.start_time = time.time()

@app.after_request
def log_request_info(response):
    duration = time.time() - g.start_time
    process = psutil.Process(os.getpid())
    mem = process.memory_info().rss / (1024*1024)
    print(f"[Request] {request.method} {request.path} | Duration: {duration:.2f}s | Memory: {mem:.2f} MB")
    return response

# ---------- PAGE ROUTES ----------
@app.get("/")
def home_page():
    return render_template("index.html")

@app.get("/query")
def query_page():
    return render_template("nlp-query.html")

# ---------- API ROUTES ----------
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

    normalized_q = normalize_query(user_q)
    prompt = build_prompt(SCHEMA, normalized_q)
    sql = generate_sql(prompt)

    if " limit " not in sql.lower():
        sql = f"{sql}\nLIMIT {DEFAULT_LIMIT}"

    safe, reason = is_safe_sql(sql)
    if not safe:
        return jsonify({
            "error": True,
            "type": "unsafe_sql",
            "message": f"Unsafe SQL: {reason}",
            "sql": sql
        }), 400
        
    print("User Query:", user_q)
    print("Normalized Query:", normalized_q)
    print("Prompt sent to Gemini:\n", prompt)
    print("Generated SQL:\n", sql)

    try:
        rows = fetch_rows(sql)

        if not rows:
            return jsonify({
                "error": True,
                "type": "no_rows",
                "message": "No matching records found for your query.",
                "sql": sql
            }), 200

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

        if error_type is None:
            error_type = "unknown_error"
            friendly_message = "Seems like something went wrong in generating your result. Please try again."

        return jsonify({
            "error": True,
            "type": error_type,
            "message": friendly_message,
            "sql": sql
        }), 400

# ---------- RUN WITH WAITRESS OR GUNICORN ----------
if __name__ == "__main__":
    import platform
    port = int(os.getenv("PORT", 5000))
    
    # Windows / local dev
    if platform.system() == "Windows":
        from waitress import serve
        print(f"Starting Waitress on http://127.0.0.1:{port}")
        serve(app, host="0.0.0.0", port=port)
    else:
        # Linux / Render / production
        print(f"Use Gunicorn to serve this app on port {port}")
        app.run(host="0.0.0.0", port=port)

