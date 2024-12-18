# financial_analyzer/core/llm.py
from langchain_google_genai import ChatGoogleGenerativeAI
from config.app_config import google_api_key


chat_model = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    google_api_key=google_api_key,
    temperature=0.7,
    max_output_tokens=2048,
    verbose=False,
    convert_system_message_to_human=True,
)