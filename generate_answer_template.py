#!/usr/bin/env python3
"""
Generate an answer file that matches the expected auto-grader format.


"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


INPUT_PATH = Path("cse_476_final_project_test_data.json")
OUTPUT_PATH = Path("cse_476_final_project_answers.json")

HEADERS = {"User-Agent": "cse476-final-project/1.0 (rshank14@asu.edu)"}


# -----------------------------
def load_questions(path: Path) -> List[Dict[str, Any]]:
    """Load questions with robust encoding handling"""
    # Try multiple encoding strategies
    encodings_to_try = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings_to_try:
        try:
            with path.open("r", encoding=encoding, errors='replace') as fp:
                data = json.load(fp)
            print(f"✓ Successfully loaded file using {encoding} encoding")
            if not isinstance(data, list):
                raise ValueError("Input file must contain a list of question objects.")
            return data
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            print(f"✗ Failed with {encoding}: {e}")
            continue
    
    # Last resort: read as binary and decode with error replacement
    try:
        with path.open("rb") as fp:
            content = fp.read()
        # Try to decode with replacement for bad bytes
        text = content.decode('utf-8', errors='replace')
        data = json.loads(text)
        print("✓ Loaded file using binary mode with error replacement")
        if not isinstance(data, list):
            raise ValueError("Input file must contain a list of question objects.")
        return data
    except Exception as e:
        raise ValueError(f"Could not load file with any encoding method: {e}")


def get_question_text(qobj: Dict[str, Any]) -> str:
    """
    Robust extraction in case the dataset uses different keys.
    """
    return (
        (qobj.get("input") or "")
        or (qobj.get("question") or "")
        or (qobj.get("prompt") or "")
        or (qobj.get("query") or "")
        or ""
    ).strip()


# -----------------------------

# -----------------------------
def plan_queries(question: str) -> List[str]:
    """
    Create 2-3 progressively simpler queries.
    This is the "PLAN" step of the agent loop.
    """
    q = (question or "").strip()
    if not q:
        return []

    # 1) quoted phrases often contain the key entity
    quoted = re.findall(r'"([^"]+)"', q)

    # 2) capitalized phrases (rough "entity" extraction)
    caps = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b", q)

    # 3) years can disambiguate
    years = re.findall(r"\b(1[6-9]\d{2}|20\d{2})\b", q)

    # 4) short fallback (first 12 words)
    words = q.split()
    short = " ".join(words[:12]).strip()

    candidates: List[str] = []
    if quoted:
        candidates.append(" ".join(quoted[:2]).strip())

    entity_bits = (caps[:3] + years[:1])
    if entity_bits:
        candidates.append(" ".join(entity_bits).strip())

    candidates.append(short)

    # De-dupe while preserving order
    out: List[str] = []
    seen = set()
    for c in candidates:
        c = (c or "").strip()
        if c and c not in seen:
            seen.add(c)
            out.append(c)

    return out[:3]


# -----------------------------

# -----------------------------
def search_wikipedia(query: str, limit: int = 6) -> List[Dict[str, Any]]:
    """
    ACT tool: Wikipedia search.
    Returns list of dicts, each includes title, pageid, snippet, etc.
    """
    try:
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": limit,
            "format": "json",
            "utf8": 1,
        }

        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("query", {}).get("search", [])
    except Exception as e:
        print(f"Search error: {e}")
        return []


def get_wikipedia_summary(pageid: int) -> str:
    """
    ACT tool: Fetch intro extract by pageid (handles redirects more cleanly).
    """
    try:
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "pageids": pageid,
            "prop": "extracts",
            "exintro": True,
            "explaintext": True,
            "redirects": 1,
            "format": "json",
            "utf8": 1,
        }

        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        pages = data.get("query", {}).get("pages", {})
        page = next(iter(pages.values())) if isinstance(pages, dict) and pages else {}
        return (page.get("extract", "") or "").strip()
    except Exception as e:
        print(f"Content error: {e}")
        return ""


# -----------------------------

# -----------------------------
def extract_answer(content: str, max_sentences: int = 2) -> str:
    """
    Extract a concise answer from content.
    """
    if not content:
        return "Information not available"

    # Basic sentence split (good enough for short intros)
    sentences = [s.strip() for s in content.split(".") if s.strip()]
    if not sentences:
        return "Information not available"

    answer = ". ".join(sentences[:max_sentences]).strip()
    if answer and not answer.endswith("."):
        answer += "."

    return answer if answer else "Information not available"


def score_candidate(question: str, title: str, snippet: Optional[str]) -> int:
    """
    OBSERVE: cheap relevance score based on token overlap.
    """
    q_words = set(re.findall(r"[A-Za-z0-9]+", (question or "").lower()))
    t_words = set(re.findall(r"[A-Za-z0-9]+", (title or "").lower()))
    s_words = set(re.findall(r"[A-Za-z0-9]+", (snippet or "").lower()))

    # Title overlap is more important than snippet overlap
    return 2 * len(q_words & t_words) + len(q_words & s_words)


# -----------------------------

# -----------------------------
def agent_loop(question: str) -> str:
    """
    Real agent loop:
    PLAN: create multiple candidate queries
    ACT: search -> fetch summary
    OBSERVE: rerank -> extract answer
    REFLECT: if answer is empty, try next plan query
    """
    try:
        q = (question or "").strip()
        if not q:
            return "Information not available"

        print(f"  Question: {q[:80]}...")

        plans = plan_queries(q)
        best_answer = ""

        for step, search_q in enumerate(plans, start=1):
            print(f"  Step {step} query: {search_q}")
            time.sleep(0.2)  # mild delay for rate limiting

            # ACT: search
            results = search_wikipedia(search_q, limit=6)
            if not results:
                continue

            # OBSERVE: rerank
            ranked = sorted(
                results,
                key=lambda r: score_candidate(q, r.get("title", ""), r.get("snippet", "")),
                reverse=True,
            )

            top = ranked[0]
            title = top.get("title", "")
            pageid = top.get("pageid")

            print(f"  Picked: {title} (pageid={pageid})")

            if not pageid:
                continue

            # ACT: fetch extract
            content = get_wikipedia_summary(int(pageid))

            # OBSERVE: extract answer
            answer = extract_answer(content, max_sentences=2)

            # REFLECT: stop early if we got a meaningful answer
            if answer != "Information not available":
                best_answer = answer
                break

        return best_answer if best_answer else "Information not available"

    except Exception as e:
        print(f"  Error: {e}")
        return "Error processing question"


# -----------------------------

# -----------------------------
def build_answers(questions: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    answers: List[Dict[str, str]] = []
    for idx, qobj in enumerate(questions, start=1):
        print(f"Processing question {idx}/{len(questions)}...")

        question_text = get_question_text(qobj)
        answer = agent_loop(question_text)

        answers.append({"output": answer})
    return answers


def validate_results(questions: List[Dict[str, Any]], answers: List[Dict[str, Any]]) -> None:
    if len(questions) != len(answers):
        raise ValueError(f"Mismatched lengths: {len(questions)} questions vs {len(answers)} answers.")
    for idx, answer in enumerate(answers):
        if "output" not in answer:
            raise ValueError(f"Missing 'output' field for answer index {idx}.")
        if not isinstance(answer["output"], str):
            raise TypeError(f"Answer at index {idx} has non-string output: {type(answer['output'])}")
        if len(answer["output"]) >= 5000:
            raise ValueError(
                f"Answer at index {idx} exceeds 5000 characters ({len(answer['output'])} chars). "
                "Please ensure your answer does not include intermediate results."
            )


def main() -> None:
    print("="*60)
    print("CSE 476 Final Project - Question Answering Agent")
    print("="*60)
    
    questions = load_questions(INPUT_PATH)

    # Helpful debug to avoid the common "wrong key -> empty query" issue
    if questions:
        print(f"\nLoaded {len(questions)} questions")
        print("First question keys:", list(questions[0].keys()))
        print("First question sample:", str(questions[0])[:100] + "...")

    answers = build_answers(questions)

    with OUTPUT_PATH.open("w", encoding="utf-8") as fp:
        json.dump(answers, fp, ensure_ascii=False, indent=2)

    with OUTPUT_PATH.open("r", encoding="utf-8") as fp:
        saved_answers = json.load(fp)

    validate_results(questions, saved_answers)
    print(f"\n{'='*60}")
    print(f"✓ SUCCESS!")
    print(f"Wrote {len(answers)} answers to {OUTPUT_PATH}")
    print(f"Format validated successfully.")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

