# financial_analyzer/core/ratio_calculator.py
from typing import TypedDict
from core.data_extractor import FinancialData

class FinancialRatios(TypedDict):
    current_ratio: float
    quick_ratio: float
    net_profit_margin: float
    roa: float
    roe: float
    asset_turnover: float
    inventory_turnover: float
    debt_to_equity: float
    interest_coverage: float


def calculate_ratios(financial_data: FinancialData) -> FinancialRatios:
    """
    Calculates financial ratios from the provided data
    :param financial_data: Dictionary containing financial figures with specific structure
    :return: Dictionary containing calculated ratios with specific structure
    """
    print("DEBUG: Starting calculate_ratios tool")
    ratios: FinancialRatios = {
        "current_ratio": financial_data.get("current_assets", 0) / financial_data.get("current_liabilities",1) if financial_data.get("current_liabilities", 1) else 0,
        "quick_ratio": (financial_data.get("current_assets", 0) - financial_data.get("inventory", 0)) / financial_data.get("current_liabilities", 1) if financial_data.get("current_liabilities", 1) else 0,
        "net_profit_margin": (financial_data.get("net_income", 0) / financial_data.get("revenue",1)) * 100 if financial_data.get("revenue", 1) else 0,
        "roa": (financial_data.get("net_income", 0) / financial_data.get("total_assets",1)) * 100 if financial_data.get("total_assets", 1) else 0,
        "roe": (financial_data.get("net_income",0) / financial_data.get("total_equity",1)) * 100 if financial_data.get("total_equity",1) else 0,
        "asset_turnover": financial_data.get("revenue",0) / financial_data.get("total_assets",1) if financial_data.get("total_assets", 1) else 0,
        "inventory_turnover": financial_data.get("cost_of_goods_sold",0) / financial_data.get("inventory",1) if financial_data.get("inventory", 1) else 0,
        "debt_to_equity": financial_data.get("total_debt",0) / financial_data.get("total_equity",1) if financial_data.get("total_equity", 1) else 0,
        "interest_coverage": financial_data.get("ebit",0) / financial_data.get("interest_expense",1) if financial_data.get("interest_expense", 1) else 0,
    }
    print("DEBUG: Finished calculate_ratios tool")
    return ratios