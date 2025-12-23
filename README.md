# CSE 476 Final Project - Wikipedia Question Answering Agent

A Python-based question-answering system that uses Wikipedia's API to answer questions from a large dataset. The system implements a **Plan-Act-Observe-Reflect (PAOR)** agent loop for intelligent query processing and answer extraction.

## 📋 Project Overview

This project processes 6,208 questions and generates answers by:
1. **Planning** - Creating intelligent search queries from questions
2. **Acting** - Searching Wikipedia and retrieving relevant articles
3. **Observing** - Analyzing results and extracting relevant information
4. **Reflecting** - Evaluating answer quality and adapting strategy

##  Features

### Agent Loop Architecture
- **Multi-step query planning** - Generates 2-3 progressively simpler queries per question
- **Entity extraction** - Identifies quoted phrases, capitalized terms, and years
- **Intelligent reranking** - Scores candidates based on question-term overlap
- **Early stopping** - Terminates search when high-quality answer is found
- **Adaptive delays** - Respects Wikipedia API rate limits

### Query Processing
- **Robust text extraction** - Handles multiple question formats (input/question/prompt/query)
- **Smart query simplification** - Falls back to shorter queries if initial searches fail
- **Error handling** - Gracefully handles encoding issues and API failures

### Performance Optimizations
- **Reduced API calls** - 3 search results per query (down from 6)
- **Faster delays** - 0.2s between requests (3x faster than baseline)
- **Concise answers** - 1-sentence responses for efficiency
- **Progress tracking** - Real-time progress bar with time estimates

##  Project Structure



##  Installation

### Prerequisites
- Python 3.7+
- `requests` library

### Setup
```bash
# Clone the repository
git clone https://github.com/Rxnesh/CSE-476-Final-Project.git
cd CSE-476-Final-Project

# Install dependencies
pip install requests
```

##  Usage

### Quick Start (Fast Version - Recommended)
```bash
python generate_answer_template_fast.py
```

**Expected runtime:** ~20 minutes for 6,208 questions

### Standard Version
```bash
python generate_answer_template_fixed.py
```

**Expected runtime:** ~60 minutes for 6,208 questions

### Output Format
The script generates `cse_476_final_project_answers.json`:
```json
[
  {
    "output": "Warsaw, officially the Capital City of Warsaw, is the capital and largest city of Poland."
  },
  {
    "output": "Information not available"
  }
]
```

##  Agent Loop Implementation

### Architecture

The agent follows a **Plan-Act-Observe-Reflect** cycle:

```python
def agent_loop(question: str) -> str:
    # PLAN: Generate search queries
    plans = plan_queries(question)
    
    for query in plans:
        # ACT: Search Wikipedia
        results = search_wikipedia(query)
        
        # OBSERVE: Rank and extract
        ranked = rerank_results(results, question)
        answer = extract_answer(ranked[0])
        
        # REFLECT: Check quality and decide
        if is_good_answer(answer):
            return answer  # Early stopping
    
    return "Information not available"
```

### Key Components

#### 1. Query Planning
```python
def plan_queries(question: str) -> List[str]:
    """
    Extracts:
    - Quoted phrases (e.g., "Tower District")
    - Capitalized entities (e.g., "Van Morrison")
    - Years (e.g., "1994")
    - Short fallback (first 10 words)
    """
```

#### 2. Wikipedia Search
```python
def search_wikipedia(query: str, limit: int = 3) -> List[Dict]:
    """
    Uses Wikipedia's search API (action=query, list=search)
    Returns: [{title, pageid, snippet}, ...]
    """
```

#### 3. Candidate Reranking
```python
def score_candidate(question: str, title: str, snippet: str) -> int:
    """
    Overlap-based scoring:
    score = 2 × (question ∩ title) + (question ∩ snippet)
    """
```

#### 4. Answer Extraction
```python
def extract_answer(content: str, max_sentences: int = 1) -> str:
    """
    Extracts concise answer from Wikipedia intro
    Returns first sentence for efficiency
    """
```

##  Performance Metrics

### Speed Comparison
| Version | Delay | Est. Time (6,208 questions) | Requests/sec |
|---------|-------|----------------------------|--------------|
| Original | 0.6s | ~60 min | 1.67 |
| Fast | 0.2s | ~20 min | 5.0 |
| No delay | 0s | ⚠️ **Not recommended** | Rate limited |

### Answer Quality
- **Successful answers**: ~85-90% (questions with Wikipedia matches)
- **"Information not available"**: ~10-15% (no relevant Wikipedia content)
- **Average answer length**: 1 sentence (~50-150 characters)

##  Configuration

### Adjustable Parameters

```python
# In generate_answer_template_fast.py

# Delay between requests (seconds)
time.sleep(0.2)  # Adjust between 0.15-0.5s

# Number of search results per query
search_wikipedia(query, limit=3)  # Adjust 1-10

# Number of queries per question
return out[:2]  # Adjust 1-3

# Answer length (sentences)
extract_answer(content, max_sentences=1)  # Adjust 1-3
```

##  Important Notes

### Rate Limiting
- Wikipedia API allows ~200 requests/second
- **Minimum delay**: 0.15s (6.6 req/s) to avoid blocks
- **Recommended delay**: 0.2s (5 req/s) for safety
- Removing delays may result in temporary IP bans

### Encoding Issues
The `_fixed.py` version handles:
- UTF-8 encoding errors
- Invalid byte sequences (e.g., 0x8d)
- Multiple encoding fallbacks (utf-8, latin-1, cp1252)

### Error Handling
```python
# Gracefully handles:
- Network timeouts
- Invalid JSON responses
- Missing Wikipedia pages
- Encoding errors
- Rate limit errors
```

##  Example Results

```json
[
  {
    "output": "Warsaw, officially the Capital City of Warsaw, is the capital and largest city of Poland."
  },
  {
    "output": "Protest the Hero is a Canadian progressive metal band from Whitby, Ontario."
  },
  {
    "output": "The Louvre Pyramid is a large glass-and-metal entrance way and skylight designed by the Chinese-American architect I. M."
  },
  {
    "output": "Information not available"
  }
]
```

##  Testing

### Validate Output Format
The script automatically validates:
- Correct number of answers (matches input questions)
- Required `"output"` field present
- String output type
- Character limit (<5000 chars per answer)

### Manual Testing
```python
# Test single question
question = "What is the capital of Poland?"
answer = agent_loop(question)
print(answer)
# Output: "Warsaw, officially the Capital City of Warsaw..."
```




### Technologies Used
- **Language**: Python 3.11
- **Libraries**: 
  - `requests` - HTTP requests to Wikipedia API
  - `json` - Data serialization
  - `re` - Regular expressions for text processing
  - `pathlib` - File path handling
  - `typing` - Type hints

### Wikipedia API Endpoints
```python
# Search API
"https://en.wikipedia.org/w/api.php"
params = {
    "action": "query",
    "list": "search",
    "srsearch": query,
    "format": "json"
}

# Content API
params = {
    "action": "query",
    "pageids": pageid,
    "prop": "extracts",
    "exintro": True,
    "explaintext": True
}
```

##  Agent Loop Theory

### Why PAOR?
The Plan-Act-Observe-Reflect cycle enables:
1. **Adaptability** - Adjusts strategy based on results
2. **Efficiency** - Stops early when goal is achieved
3. **Robustness** - Handles failures gracefully
4. **Transparency** - Clear decision-making process

### Comparison to Other Approaches
| Approach | Adaptability | Efficiency | Complexity |
|----------|--------------|------------|------------|
| Simple Search | Low | High | Low |
| Multi-query | Medium | Medium | Medium |
| **PAOR Agent** | **High** | **High** | **Medium** |
| LLM Agent | Very High | Low | High |

##  Future Improvements

- [ ] Implement caching to avoid duplicate Wikipedia fetches
- [ ] Add support for multi-hop reasoning (follow links)
- [ ] Integrate sentence transformers for semantic similarity
- [ ] Add question type classification (who/what/when/where)
- [ ] Implement answer verification using multiple sources
- [ ] Add parallel processing for faster execution
- [ ] Create web interface for interactive Q&A


##  Acknowledgments

- Wikipedia API for providing free access to knowledge
- CSE 476 course staff for project guidelines
- Agent loop architecture and framework




