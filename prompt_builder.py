from typing import Dict, List

# Tailored to your schema (college_profiles, alumni_reviews), but generic enough for others.
def build_prompt(schema: Dict[str, List[str]], user_query: str) -> str:
    schema_lines = []
    for table, cols in schema.items():
        schema_lines.append(f"- {table}({', '.join(cols)})")
    schema_text = "\n".join(schema_lines)

    prompt = f"""
You are an expert PostgreSQL query generator. Output ONLY one safe, read-only SQL query in PostgreSQL dialect, with no explanations.

DATABASE SCHEMA (public):
{schema_text}

USER REQUEST:
\"\"\"{user_query}\"\"\"

REQUIREMENTS:
- Use explicit JOINs with ON for relationships.
- If selecting parent rows (e.g., colleges) with related child rows (e.g., alumni_reviews), return one row per parent and aggregate child rows into a JSON array using JSON_AGG(JSON_BUILD_OBJECT(...)).
- Apply FILTER (WHERE ...) directly to JSON_AGG, NOT inside JSON_BUILD_OBJECT. 
  *Correct:* 
    COALESCE(
      JSON_AGG(JSON_BUILD_OBJECT('id', ar.id, 'name', ar.name)) FILTER (WHERE ar.id IS NOT NULL),
      '[]'
    )
  *Incorrect:* 
    COALESCE(
      JSON_AGG(JSON_BUILD_OBJECT('id', ar.id, 'name', ar.name) FILTER (WHERE ar.id IS NOT NULL)),
      '[]'
    )
- Always wrap JSON_AGG in COALESCE(..., '[]') to return an empty array when no rows exist.
- To include parent rows even when there are zero matching child rows, use LEFT JOIN and put child filters in the JOIN condition, not in WHERE.
- Use exact column names as shown in the schema.
- Never modify data. Only SELECT/CTE allowed. No semicolons. Add LIMIT 500 if not specified.
- Do not include comments or explanations.
- Do not include semicolons at the end of the query.
- The first token of the query must be SELECT or WITH.
- If only one table is needed, use a simple SELECT with LIMIT 500.
- When using JSON_AGG with non-aggregated parent columns, add a GROUP BY including every selected parent column.



Only output the SQL. No commentary.
"""
    return prompt
