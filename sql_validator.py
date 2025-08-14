import re
import sqlparse

# Small denylist. Removed pg_\w+ so legitimate columns like pg_fee won't be blocked.
BAD_WORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|GRANT|REVOKE|COPY)\b",
    re.I,
)

def is_safe_sql(sql_text: str):
    if not sql_text or not isinstance(sql_text, str):
        return False, "Empty SQL"

    # No semicolons -> single statement only
    if ";" in sql_text.strip():
        return False, "Semicolon / multiple statements not allowed"

    if BAD_WORDS.search(sql_text):
        return False, "Disallowed keyword detected"

    parsed = sqlparse.parse(sql_text)
    if not parsed:
        return False, "Could not parse SQL"

    stmt = parsed[0]
    first = stmt.token_first(skip_cm=True)
    if not first:
        return False, "Empty statement"

    if first.value.upper() not in {"SELECT", "WITH"}:
        return False, "Only SELECT / WITH queries are allowed"

    return True, None
