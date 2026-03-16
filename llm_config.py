import asyncio
import os

from cerebras.cloud.sdk import Cerebras
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

load_dotenv()

# LangSmith Tracing Configuration
if os.getenv("LANGCHAIN_API_KEY"):
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
    # LANGCHAIN_PROJECT should be set in .env


def get_gemini_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0,
    )


def get_groq_llm():
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        groq_api_key=os.getenv("GROQ_API_KEY"),
        temperature=0,
    )


# def get_openrouter_llm():
#     return ChatOpenAI(
#         model="gpt-4o-mini",
#         api_key=os.getenv("OPENAI_API_KEY"),
#         temperature=0,
#     )


class CerebrasLLM:
    def __init__(self):
        self.client = Cerebras(api_key=os.getenv("CEREBRAS_API_KEY"))

    def _call(self, prompt: str):
        response = self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a structured data extraction assistant.",
                },
                {"role": "user", "content": prompt},
            ],
            model="llama3.1-8b",  # use model available in your account
            max_completion_tokens=1024,
            temperature=0,
            top_p=1,
            stream=False,
        )

        content = response.choices[0].message.content
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }

        # Return LangChain-like object with content and usage_metadata
        return type(
            "LLMResponse",
            (),
            {"content": content, "response_metadata": {"token_usage": usage}},
        )()

    def invoke(self, prompt: str):
        return self._call(prompt)

    async def ainvoke(self, prompt: str):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._call, prompt)


def get_cerebras_llm():
    return CerebrasLLM()
