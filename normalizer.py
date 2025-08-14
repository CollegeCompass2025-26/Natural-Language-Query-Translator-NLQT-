from typing import Dict, List

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

QUALITATIVE_THRESHOLDS = {
    "excellent": "> 8",
    "top": "> 8",
    "best": "> 8",
    "high": "> 7",
    "good": "> 6",
    "decent": "> 5",
    "average": "~ 5",  # could leave for LLM to interpret
    "poor": "< 4",
    "bad": "< 4",
    "worst": "< 3",
    "low": "< 4",
    "cheap": "< 200000",  # example fee threshold
    "affordable": "< 300000",
    "expensive": "> 500000",
    "costly": "> 500000"
}

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

    return normalized
