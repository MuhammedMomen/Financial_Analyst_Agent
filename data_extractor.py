# financial_analyzer/core/data_extractor.py
from typing import TypedDict
from langchain.schema import HumanMessage
from core.llm import chat_model
import json
import re


# Define type structures for Gemini
class FinancialData(TypedDict):
    current_assets: float
    current_liabilities: float
    total_assets: float
    total_equity: float
    net_income: float
    inventory: float
    total_debt: float
    ebit: float
    interest_expense: float
    revenue: float
    cost_of_goods_sold: float


def extract_financial_data_from_text(text: str) -> FinancialData:
    """
    Extracts financial data from text using LLM
    :param text: Text extracted from PDF files
    :return: Dictionary containing financial data with specific structure
    """
    print("DEBUG: Starting extract_financial_data_from_text")
    prompt = f"""
        You are an expert financial analyst.
        Given the following text, extract the key financial figures and return them in JSON format.
        Do not give explanations or any text that is not JSON.
        If a value is not present in the text, do not provide the field, return only the fields that are extracted from the text.

        Text: {text}

        Format the extracted information as a JSON object with these keys:
        {{
            "current_assets": float,
            "current_liabilities": float,
            "total_assets": float,
            "total_equity": float,
            "net_income": float,
            "inventory": float,
            "total_debt": float,
            "ebit": float,
            "interest_expense": float,
            "revenue": float,
            "cost_of_goods_sold": float
        }}

        JSON:
        """

    try:
        response = chat_model.invoke([HumanMessage(content=prompt)]).content
        print(f"DEBUG: LLM Response: {response}")
        # Remove markdown code blocks if present
        response = re.sub(r'```(json)?', '', response).strip()
        financial_data = json.loads(response)
        print(f"DEBUG: Successfully parsed financial data: {financial_data}")
        return financial_data
    except json.JSONDecodeError:
        print(f"ERROR: JSON Decode Error: Could not decode JSON from LLM response: {response}")
        return None
    except Exception as e:
        print(f"ERROR: An error occurred while processing the LLM response: {e}")
        return None
    finally:
        print("DEBUG: Finished extract_financial_data_from_text")