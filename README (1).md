# CSE 476 Final Project - Wikipedia QA Agent

A simple question-answering agent that uses Wikipedia to answer test questions.

## What It Does

The agent searches Wikipedia for each question and returns a short answer from the most relevant article.

## Requirements

- Python 3.7+
- `requests` library

## Setup

1. **Install Python** (if you don't have it)

2. **Install the requests library:**

Windows:
```bash
pip install requests
```

Mac/Linux:
```bash
pip3 install requests
```

## Running the Code

1. Put these files in the same folder:
   - `generate_answer_template.py`
   - `cse_476_final_project_test_data.json`

2. Run the script:

Windows:
```bash
python generate_answer_template.py
```

Mac/Linux:
```bash
python3 generate_answer_template.py
```

3. Wait for it to finish (takes about 30 minutes for all 6208 questions)

4. The output file `cse_476_final_project_answers.json` will be created

## How It Works

1. For each question, search Wikipedia for relevant articles
2. Get the intro section of the top result
3. Extract the first 2-3 sentences as the answer
4. Save all answers to a JSON file

## Files

- `generate_answer_template.py` - Main code with the agent
- `cse_476_final_project_test_data.json` - Input questions
- `cse_476_final_project_answers.json` - Output answers (generated)

## Troubleshooting

**"No module named 'requests'"**
- Install it: `pip install requests`

**"FileNotFoundError: cse_476_final_project_test_data.json"**
- Make sure the test data file is in the same folder

**"Search error" messages during running**
- This is normal - Wikipedia is rate limiting the requests
- The script handles it and keeps going

## Output Format

The output is a JSON file with this format:
```json
[
  {"output": "Answer to question 1..."},
  {"output": "Answer to question 2..."},
  
]
```

Each answer is just text, no extra formatting or reasoning included.
