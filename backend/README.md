# AI Self-Reflection Backend

A FastAPI backend service that provides AI responses with self-reflection and confidence scoring. The system evaluates AI-generated answers across three dimensions: completeness, accuracy, and reasoning quality.

## 🏗️ Architecture Overview

```
backend/
├── core/                           # Core application modules
│   ├── answer_and_reflect/        # Self-reflection system
│   │   ├── respond_score.py       # Main reflection logic
│   │   ├── types.py               # Pydantic models and types
│   │   ├── exceptions.py          # Custom exceptions
│   │   └── prompts.yaml          # Reflection prompts configuration
│   ├── api/                       # API layer
│   │   ├── chat.py               # Chat endpoints
│   │   └── routers.py            # Router configuration
│   ├── config.py                 # Configuration management
│   └── intelligence.py           # OpenAI client factory
├── main.py                       # FastAPI application entry point
├── requirements.txt              # Python dependencies
└── pyproject.toml               # Project configuration
```

## 🚀 Quick Start

### 1. Environment Setup

Copy the environment template and configure your OpenAI API key:

```bash
cp .env.template .env.local
```

Edit `.env.local` with your values:
```bash
OPENAI_API_KEY=your-openai-api-key-here
MODEL=gpt-4o-mini  # or your preferred model
MAX_RETRIES=3
PROMPTS_FILE=core/answer_and_reflect/prompts.yaml
```

### 2. Install Dependencies

**Option A: Using uv (recommended)**
```bash
uv sync
source .venv/bin/activate
```

**Option B: Using pip**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Start the Server

```bash
uvicorn main:app --reload --port 8087
```

The API will be available at:
- **API Base**: http://localhost:8087
- **Interactive Docs**: http://localhost:8087/docs
- **OpenAPI Schema**: http://localhost:8087/openapi.json

## 📡 API Endpoints

### Base Endpoints

- `GET /` - Health check endpoint
- `GET /docs` - Interactive API documentation

### Chat Endpoints

#### 1. Basic Reflection: `/api/chat/chat_with_score`

**Purpose**: Fast, cost-optimized responses with basic self-reflection
**Features**:
- ✅ Basic reflection scoring
- ✅ Static reasoning from YAML prompts
- ✅ Optimized for speed and cost
- ✅ Manual error handling

**Request**:
```bash
curl -X POST "http://localhost:8087/api/chat/chat_with_score" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is 2+2?"}'
```

**Response Structure**:
```json
{
  "base_response": {
    "id": "chatcmpl-...",
    "choices": [{"message": {"content": "2 + 2 equals 4."}}],
    "model": "gpt-4o-mini-2024-07-18",
    "usage": {"total_tokens": 22}
  },
  "reflection_response": {
    "completeness": {"rating": "A", "reason": "My answer fully addresses the question"},
    "accuracy": {"rating": "A", "reason": "All facts are true to the best of my knowledge"},
    "reasoning": {"rating": "A", "reason": "My reasoning is sound and well-structured"},
    "numerical_score": 1.0
  }
}
```

#### 2. Advanced Reflection: `/api/chat/chat_with_score_reflect_and_reason`

**Purpose**: Detailed responses with AI-generated reasoning
**Features**:
- ✅ Advanced reflection with AI-generated reasoning
- ✅ Structured extraction using Instructor
- ✅ Comprehensive error handling
- ⚠️ Higher latency and cost

**Request**:
```bash
curl -X POST "http://localhost:8087/api/chat/chat_with_score_reflect_and_reason" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the capital of France?"}'
```

**Response Structure**: Same as basic endpoint, but with AI-generated reasoning in reflection fields.

## 🔧 Core Components

### Self-Reflection System

The system evaluates responses across three dimensions:

1. **Completeness** (`core/answer_and_reflect/types.py:22-24`)
   - How well the answer addresses the user's question
   - Ratings: A (complete), B (incomplete), C (partial)

2. **Accuracy** (`core/answer_and_reflect/types.py:25-27`)
   - Confidence in factual correctness
   - Ratings: A (certain), B (uncertain), C (mostly certain)

3. **Reasoning** (`core/answer_and_reflect/types.py:28-30`)
   - Quality of logical reasoning
   - Ratings: A (sound), B (flawed), C (generally sound)

### Scoring Algorithm (`core/answer_and_reflect/types.py:92-104`)

```python
# Letter grades converted to numerical scores
grade_values = {"A": 1.0, "B": 0.0, "C": 0.5}
numerical_score = average(completeness, accuracy, reasoning)
```

### Configuration Management

- **Environment Variables**: Loaded via `core/config.py`
- **Prompts Configuration**: Managed in `core/answer_and_reflect/prompts.yaml`
- **Model Settings**: Configurable OpenAI model and retry settings

## 🛠️ Development

### Code Quality Tools

```bash
# Linting and formatting
ruff check .
ruff format .

# Type checking
mypy .
```

### Project Structure

- **FastAPI Application**: `main.py` - Application entry point with CORS middleware
- **API Routes**: `core/api/` - RESTful endpoint definitions
- **Business Logic**: `core/answer_and_reflect/` - Core reflection algorithms
- **Configuration**: `core/config.py` - Environment and settings management
- **Dependencies**: `core/intelligence.py` - External service integrations

### Error Handling (`core/answer_and_reflect/exceptions.py`)

Custom exceptions for robust error handling:
- `NoLetterGradesFound` - Missing reflection grades
- `LetterGradesNotThreeCharactersLong` - Invalid grade format
- `InvalidLetterGrade` - Invalid grade values
- `RetryException` - Triggering automatic retries

## 🔄 Usage Examples

### Simple Question
```bash
curl -X POST "http://localhost:8087/api/chat/chat_with_score" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Python?"}'
```

### Complex Analysis
```bash
curl -X POST "http://localhost:8087/api/chat/chat_with_score_reflect_and_reason" \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain the differences between supervised and unsupervised machine learning with examples."}'
```

### Counting Task (from original README)
```bash
curl -X POST "http://localhost:8087/api/chat/chat_with_score_reflect_and_reason" \
  -H "Content-Type: application/json" \
  -d '{"query": "How many syllables are in the phrase: \"How much wood could a woodchuck chuck if a woodchuck could chuck wood\"? Answer with a single number only."}'
```

## ⚙️ Configuration Options

### Environment Variables
- `OPENAI_API_KEY` - Your OpenAI API key (required)
- `MODEL` - OpenAI model to use (default: gpt-4o-mini)
- `MAX_RETRIES` - Maximum retry attempts (default: 3)
- `PROMPTS_FILE` - Path to prompts YAML file

### Customizing Prompts

Edit `core/answer_and_reflect/prompts.yaml` to modify:
- System prompts for reflection
- Reason codes for different ratings
- User message templates

## 🚦 Production Considerations

- **Rate Limiting**: Implement rate limiting for production use
- **Authentication**: Add API key authentication
- **Monitoring**: Add logging and metrics collection
- **Caching**: Consider caching for repeated queries
- **Error Reporting**: Integrate error tracking service