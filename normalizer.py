from typing import Dict, List
import re
# Step 1: Synonyms / fuzzy keywords
FUZZY_KEYWORDS: Dict[str, List[str]] = {
    "college": ["college name", "institute", "university", "campus", "school", "institution"],
    "state": ["location", "region", "province", "area", "state name"],
    "stream": ["branch", "department", "discipline", "course category", "field of study", "major"],
    "ug_fee": ["undergraduate fee", "bachelor fee", "ug cost", "tuition for undergrad", "bachelor tuition"],
    "pg_fee": ["postgraduate fee", "master fee", "pg cost", "tuition for masters", "graduate tuition"],
    "rating": ["overall rating", "score", "rank", "stars", "review score"],
    "academic": ["academics", "study quality", "curriculum", "academic excellence", "course content"],
    "accommodation": ["hostel", "housing", "dormitory", "student residence", "accommodations"],
    "faculty": ["teachers", "professors", "staff", "mentors", "faculty quality"],
    "infrastructure": ["facilities", "buildings", "campus infra", "infrastructure quality", "labs"],
    "placement": ["placements", "job offers", "recruitment", "career support", "company offers", "hiring stats"],
    "social_life": ["campus life", "student activities", "events", "fun", "festivals", "social scene"]
}

# Step 2: Qualitative descriptors → explicit conditions
QUALITATIVE_THRESHOLDS = {
    "excellent": "> 8",
    "top": "> 8",
    "best": "> 8",
    "high": "> 7",
    "good": "> 6",
    "decent": "> 5",
    "average": "~ 5",  # could leave ambiguous for LLM to handle
    "poor": "< 4",
    "bad": "< 4",
    "worst": "< 3",
    "low": "< 4",
    "cheap": "< 200000",
    "affordable": "< 300000",
    "expensive": "> 500000",
    "costly": "> 500000"
}

def apply_fuzzy_keywords(query: str) -> str:
    """Replace fuzzy terms with canonical column names."""
    normalized = query
    for column, synonyms in FUZZY_KEYWORDS.items():
        for syn in synonyms:
            if syn in normalized:
                normalized = normalized.replace(syn, column)
    return normalized

def apply_qualitative_thresholds(query: str) -> str:
    """Replace qualitative adjectives with explicit numeric conditions."""
    normalized = query
    for word, condition in QUALITATIVE_THRESHOLDS.items():
        if word in normalized:
            normalized = normalized.replace(word, condition)
    return normalized

def normalize_comparators(query: str) -> str:
    """Convert natural language comparators into SQL symbols."""
    q = query

    patterns = [
        (r"(greater than|above|more than)\s+(\d+)", r"> \2"),
        (r"(less than|below|under)\s+(\d+)", r"< \2"),
        (r"(at least|min(?:imum)?)\s+(\d+)", r">= \2"),
        (r"(at most|max(?:imum)?)\s+(\d+)", r"<= \2")
    ]
    for pat, repl in patterns:
        q = re.sub(pat, repl, q)

    # Handle lakh/crore conversions
    def convert_money(match):
        amount = int(match.group(1))
        unit = match.group(2)
        if unit.startswith("lakh"):
            amount *= 100000
        elif unit.startswith("crore"):
            amount *= 10000000
        return str(amount)

    q = re.sub(r"(\d+)\s*(lakh|lakhs|crore|crores)", convert_money, q)

    return q

IMPLICIT_REFERENCES = {
    "best": "rating",
    "top": "rating",
    "ranked": "rating",
    "cheap": "ug_fee",
    "affordable": "ug_fee",
    "expensive": "ug_fee",
    "costly": "ug_fee",
    "fees": "ug_fee",         # default if not specified
    "placements": "placement",
    "jobs": "placement"
}

CITIES_AND_STATES = [
    "maharashtra", "karnataka", "pune", "mumbai", "delhi", "tamil nadu"
    # Extend this as needed
]

def apply_implicit_references(query: str) -> str:
    """Insert missing column references when users use vague terms."""
    q = query

    # If query says 'best' or 'top' but no column specified → assume rating
    if any(word in q for word in ["best", "top", "ranked"]) and "rating" not in q:
        q += " rating"

    # If query mentions fees but no UG/PG → default to ug_fee
    if "fee" in q and "ug_fee" not in q and "pg_fee" not in q:
        q = q.replace("fee", "ug_fee")

    # If query mentions city/state → map implicitly to state column
    for loc in CITIES_AND_STATES:
        if loc in q and "state" not in q:
            q = q.replace(loc, f"state = {loc}")

    # Handle cheap/affordable/expensive → ensure ug_fee column
    for word in ["cheap", "affordable", "expensive", "costly"]:
        if word in q and "ug_fee" not in q:
            q += " ug_fee"

    return q

def apply_logical_operators(query: str) -> str:
    """
    Normalize logical operators (and/or/not) into SQL-friendly syntax.
    - Replaces ' and ' → ' AND '
    - Replaces ' or ' → ' OR '
    - Replaces ' not ' → ' NOT '
    - Handles 'with' and 'having' cases too
    """
    q = query

    # Make replacements only when these words appear as standalone tokens
    logical_map = {
        r"\band\b": "AND",
        r"\bor\b": "OR",
        r"\bnot\b": "NOT",
        r"\bwith\b": "AND",       # treat "with" as AND condition
        r"\bhaving\b": "AND"      # some users might say "colleges having good placement"
    }

    for pat, repl in logical_map.items():
        q = re.sub(pat, repl, q)

    return q

def normalize_query(user_query: str) -> str:
    normalized = user_query.lower()

    # Step 1: replace synonyms with exact DB column names
    for column, synonyms in FUZZY_KEYWORDS.items():
        for syn in synonyms:
            if syn in normalized:
                normalized = normalized.replace(syn, column)

    # Step 2: replace qualitative adjectives with explicit conditions
    for word, condition in QUALITATIVE_THRESHOLDS.items():
        if word in normalized:
            normalized = normalized.replace(word, condition)

    # Step 3: handle comparators
    normalized = normalize_comparators(normalized)
    
    # Step 4: handle implicit references
    normalized = apply_implicit_references(normalized)
    
    # Step 5: normalize logical operators
    normalized = apply_logical_operators(normalized)

    return normalized
