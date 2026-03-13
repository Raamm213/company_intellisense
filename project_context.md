# Company Intelligence Analyst Project

## Overview
This is a Python-based corporate intelligence tool that extracts structured company profiles using multiple Large Language Models (LLMs) simultaneously. The tool allows a user to input a company name, parallelly prompts three different LLMs (Google Gemini, Groq, and OpenRouter), parses their responses into a predefined Pydantic schema, and outputs the collective findings into both the terminal and a saved JSON file.

## Tech Stack
- **Language**: Python 3
- **Core Library**: `langchain`, `langchain-core`, `langchain-openai`, `langchain-google-genai`, `langchain-groq`
- **Schema Validation**: `pydantic`
- **Environment Management**: `python-dotenv`

## Project Structure
The project consists of the following key files:

### 1. `schema.py`
Defines the data structure we want to extract from the LLMs using Pydantic. 
Fields extracted:
- `name` (str)
- `short_name` (Optional[str])
- `industry` (Optional[str])
- `incorporation_year` (Optional[str])
- `headquarters_address` (Optional[str])
- `annual_revenue` (Optional[str])
- `ceo_name` (Optional[str])
- `website_url` (Optional[str])

### 2. `llm_config.py`
Configures and initializes the connections to three different LLM providers using LangChain. 
Models used:
- **Gemini**: `gemini-2.5-flash` using `ChatGoogleGenerativeAI`
- **Groq**: `llama-3.3-70b-versatile` using `ChatGroq`
- **OpenRouter**: `mistralai/mistral-7b-instruct` using `ChatOpenAI` (with a custom base URL `https://openrouter.ai/api/v1` and `sk-or-` prefixed API key)

### 3. `main.py`
The entry point of the application.
- Uses `PydanticOutputParser` to inject the schema format instructions into the prompt.
- `PromptTemplate` instructs the LLM to act as a corporate intelligence analyst and return ONLY valid JSON matching the schema.
- Iterates over all configured models, invokes them with the prompt, and extracts the structured JSON.
- Safely catches parsing errors if an LLM outputs malformed data.
- Saves the final aggregated output as a sanitized JSON file locally (e.g., `apple_intel.json`).

### 4. `.env` (Not tracked in version control)
Contains the API keys used for authentication:
- `GEMINI_API_KEY`
- `GROQ_API_KEY`
- `OPENROUTER_API_KEY`
- `OPENAI_API_KEY` (Often mirrors OPENROUTER_API_KEY for OpenRouter functionality)

## How It Works
1. Run `python main.py`
2. Enter the name of a company (e.g., "Meta" or "Apple").
3. The script sends the request to Gemini, Groq, and OpenRouter.
4. Each model attempts to extract the required fields and returns a JSON object.
5. The combined result from all three models is displayed in the terminal.
6. A permanent JSON file (e.g., `meta_intel.json`) is deposited in the main directory.

## Current State & Next Steps
- The application currently works seamlessly in the terminal and generates JSON artifacts.
- Future improvements could involve adding async calls to speed up the multi-LLM fetching process, adding more fields to extract, or building a front-end view for the gathered intelligence.
