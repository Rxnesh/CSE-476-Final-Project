#!/usr/bin/env python3
"""
Generate a placeholder answer file that matches the expected auto-grader format.

"""

from __future__ import annotations

import json
import requests
import time
from pathlib import Path
from typing import Any, Dict, List


INPUT_PATH = Path("cse_476_final_project_test_data.json")
OUTPUT_PATH = Path("cse_476_final_project_answers.json")

HEADERS = {
    "User-Agent": "cse476-final-project/1.0 (rshank14@asu.edu)"
}


def load_questions(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fp:
        data = json.load(fp)
    if not isinstance(data, list):
        raise ValueError("Input file must contain a list of question objects.")
    return data


def search_wikipedia(query: str, limit: int = 3) -> List[str]:
    "Search Wikipedia and return list of article titles."
    try:
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "opensearch",
            "search": query,
            "limit": limit,
            "format": "json",
        }

        # Add headers and basic error check 
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        results = response.json()
        return results[1]
    except Exception as e:
        print(f"Search error: {e}")
        return []


def get_wikipedia_summary(title: str) -> str:
    "Get a summary of a Wikipedia article."
    try:
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "titles": title,
            "prop": "extracts",
            "exintro": True,
            "explaintext": True,
            "format": "json",
        }

        # Add headers and basic error check 
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        pages = data["query"]["pages"]
        page = next(iter(pages.values()))
        return page.get("extract", "")
    except Exception as e:
        print(f"Content error: {e}")
        return ""


def extract_answer(content: str, max_sentences: int = 3) -> str:
    "Extract a concise answer from content."
    if not content:
        return "Information not available"

    # Split sentences and take few
    sentences = content.split(".")
    answer = ".".join(sentences[:max_sentences])

    # Ends with period
    if answer and not answer.endswith("."):
        answer += "."

    return answer if answer else "Information not available"


def agent_loop(question: str) -> str:
    "Agent loop that searches Wikipedia and extracts an answer."
    try:
        print(f"  Query: {question[:60]}...")
        time.sleep(0.5)  # Add time to avoid rate limiting

        # Search wikipedia
        search_results = search_wikipedia(question)

        if not search_results:
            return "Information not available"

        # Get the article's summary
        article_title = search_results[0]
        print(f"  Found: {article_title}")
        content = get_wikipedia_summary(article_title)

        # Get exact answer
        answer = extract_answer(content, max_sentences=2)

        return answer

    except Exception as e:
        print(f"  Error: {e}")
        return "Error processing question"


def build_answers(questions: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    answers = []
    for idx, question in enumerate(questions, start=1):
        print(f"Processing question {idx}/{len(questions)}...")

        # Question text
        question_text = question.get("input", "")

        # Run agent loop
        answer = agent_loop(question_text)

        # Add it to the results
        answers.append({"output": answer})

    return answers


def validate_results(
    questions: List[Dict[str, Any]], answers: List[Dict[str, Any]]
) -> None:
    if len(questions) != len(answers):
        raise ValueError(
            f"Mismatched lengths: {len(questions)} questions vs {len(answers)} answers."
        )
    for idx, answer in enumerate(answers):
        if "output" not in answer:
            raise ValueError(f"Missing 'output' field for answer index {idx}.")
        if not isinstance(answer["output"], str):
            raise TypeError(
                f"Answer at index {idx} has non-string output: {type(answer['output'])}"
            )
        if len(answer["output"]) >= 5000:
            raise ValueError(
                f"Answer at index {idx} exceeds 5000 characters "
                f"({len(answer['output'])} chars). Please make sure your answer does not include any intermediate results."
            )


def main() -> None:
    questions = load_questions(INPUT_PATH)
    answers = build_answers(questions)

    with OUTPUT_PATH.open("w") as fp:
        json.dump(answers, fp, ensure_ascii=False, indent=2)

    with OUTPUT_PATH.open("r") as fp:
        saved_answers = json.load(fp)
    validate_results(questions, saved_answers)
    print(
        f"Wrote {len(answers)} answers to {OUTPUT_PATH} "
        "and validated format successfully."
    )


if __name__ == "__main__":
    main()
