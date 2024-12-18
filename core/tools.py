# ./core/tools.py
from langchain.tools import tool
from typing import List
from core.data_extractor import FinancialData
from core.pdf_processor import load_and_extract_text_from_pdfs
from core.data_extractor import extract_financial_data_from_text
from core.ratio_calculator import calculate_ratios,FinancialRatios
from core.report_generator import generate_pdf_report


@tool("get_financial_data")
def get_financial_data(pdf_paths: List[str], upload_dir: str) -> FinancialData:
    """
    Extracts financial data from the provided PDF paths using the LLM
    :param pdf_paths: List of paths to the financial report pdf files
    :return: Dictionary containing financial data with specific structure
    """
    print("DEBUG: Starting get_financial_data tool")
    extracted_text = load_and_extract_text_from_pdfs(pdf_paths, upload_dir)
    if not extracted_text:
        print("DEBUG: No text extracted, cannot proceed")
        raise ValueError("No text extracted from PDFs.")
    financial_data = extract_financial_data_from_text(extracted_text)
    if financial_data is None:
        print("DEBUG: Financial data extraction failed")
        raise ValueError("Could not extract financial data from the given text.")
    print("DEBUG: Finished get_financial_data tool")
    return financial_data


@tool("calculate_ratios")
def calculate_ratios_tool(financial_data: FinancialData) -> FinancialRatios:
    """
    Calculates financial ratios from the provided data
    :param financial_data: Dictionary containing financial figures with specific structure
    :return: Dictionary containing calculated ratios with specific structure
    """
    print("DEBUG: Starting calculate_ratios tool")
    ratios = calculate_ratios(financial_data)
    print("DEBUG: Finished calculate_ratios tool")
    return ratios


@tool("generate_pdf_report")
def generate_pdf_report_tool(ratios: FinancialRatios) -> str:
    """
    Generates PDF report with financial ratios and explanations
    :param ratios: Dictionary containing calculated ratios with specific structure
    :return: Path to generated PDF file
    """
    print("DEBUG: Starting generate_pdf_report tool")
    report_path = generate_pdf_report(ratios)
    print("DEBUG: Finished generate_pdf_report tool")
    return report_path