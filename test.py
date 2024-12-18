# financial_analyzer/main.py
import flet as ft
import os
from ui import main as ui_main
from config.app_config import flet_secret_key
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import threading
import uvicorn
from pathlib import Path

# Create directories
UPLOAD_DIR = Path("upload_dir")
OUTPUT_DIR = Path("output")

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

app = FastAPI()

# Mount output directory for static file serving
app.mount("/output", StaticFiles(directory="output"), name="output")

@app.get("/download/{filename}")
async def download(filename: str):
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        return {"error": "File not found"}
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/pdf',
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

if __name__ == "__main__":
    # Set FLET_SECRET_KEY as environment variable
    os.environ["FLET_SECRET_KEY"] = flet_secret_key

    # Run FastAPI server in separate thread
    threading.Thread(
        target=lambda: uvicorn.run(
            app,
            host="127.0.0.1",
            port=8000
        ),
        daemon=True
    ).start()

    # Run Flet app
    ft.app(
        target=ui_main.main, 
        view=ft.AppView.WEB_BROWSER,
        assets_dir="assets",
        upload_dir=str(UPLOAD_DIR),
        port=8550
    )

# ./ui/main.py
import flet as ft
import os
from typing import List
import shutil
from core.agent import process_financial_analysis
from config.app_config import google_api_key,flet_secret_key
from ui.components import create_api_key_field, create_file_display_text, create_upload_button, create_step_text, create_submit_button, create_download_button
from flet import FilePickerUploadFile, FilePickerResultEvent
import uuid

def main(page: ft.Page):
    page.title = "Financial Statement Analysis App"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.window_width = 700
    page.window_height = 800
    page.theme = ft.theme.Theme(color_scheme_seed='blue')

    # Create directories
    upload_dir = "upload_dir"
    output_dir = "output"
    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    # Variables for storing state
    uploaded_files = []
    api_key = google_api_key if google_api_key else ''
    is_processing = False
    output_filename = None
    state = type('state', (object,), {
        "api_key": api_key
    })()

    def on_upload_callback(e):
        if e.error:
            print(f"ERROR: Upload error for file: {e.file_name}: {e.error}")
            page.show_snack_bar(ft.SnackBar(ft.Text(f"Error uploading file: {e.file_name}, Error:{e.error}", font_family='Roboto'), open=True))
        else:
            print(f"DEBUG: File {e.file_name} uploaded successfully.")

    file_picker = ft.FilePicker(
        on_result=lambda e: on_files_selected(e),
        on_upload=on_upload_callback
    )
    page.overlay.append(file_picker)

    file_display_text = create_file_display_text()

    def update_file_display(file_names):
        if file_names:
            display_text = f"Files selected: {', '.join(file_names)}"
            file_display_text.value = display_text
            file_display_text.color = "black"
        else:
            file_display_text.value = "No PDF file(s) selected."
            file_display_text.color = "grey"
        page.update()

    def open_file_picker(e):
        file_picker.pick_files(
            allow_multiple=True,
            allowed_extensions=['pdf'],
        )

    def on_files_selected(e: FilePickerResultEvent):
        if e.files:
            uploaded_files.clear()
            upload_list = []
            for file in e.files:
                upload_url = page.get_upload_url(file.name, 600)
                upload_list.append(
                    FilePickerUploadFile(
                        file.name,
                        upload_url=upload_url,
                    )
                )
                uploaded_files.append(file.name)

            file_picker.upload(upload_list)
            file_names = [file.name for file in e.files]
            update_file_display(file_names)

    api_key_field = create_api_key_field(api_key, lambda e: on_api_change(e))
    step_text = create_step_text()

    def handle_download_click(e):
        nonlocal output_filename
        if output_filename:
            try:
                base_url = "http://127.0.0.1:8000"
                download_url = f"{base_url}/download/{output_filename}"
                page.launch_url(download_url)
                step_text.value = "Download started!"
            except Exception as ex:
                step_text.value = f"Download error: {str(ex)}"
            page.update()

    download_button = create_download_button(handle_download_click)
    download_button.visible = False

    def run_analysis(e):
        nonlocal output_filename
        if not state.api_key:
            page.show_snack_bar(ft.SnackBar(
                ft.Text("Please provide the api key", font_family='Roboto'),
                open=True,
            ))
        elif not uploaded_files:
            page.show_snack_bar(ft.SnackBar(
                ft.Text("Please upload at least 1 PDF file.", font_family='Roboto'),
                open=True,
            ))
        else:
            page.update()

            try:
                step_text.value = "Extracting Data..."
                page.update()
                full_paths = [os.path.join(upload_dir, file) for file in uploaded_files]
                analysis_result = process_financial_analysis(full_paths, state.api_key, upload_dir)

                if isinstance(analysis_result, str):
                    try:
                        output_filename = f"{uuid.uuid4()}.pdf"
                        output_path = os.path.join(output_dir, output_filename)
                        shutil.copy(analysis_result, output_path)
                        os.remove(analysis_result)  # Remove original file
                        
                        step_text.value = "Report Generated Successfully"
                        download_button.visible = True
                        page.update()
                    except Exception as e:
                        print(f"ERROR: Error copying report: {e}")
                        step_text.value = "Error Generating Report"
                        page.update()
                        page.show_snack_bar(ft.SnackBar(
                            ft.Text("Failed to generate report", font_family='Roboto'),
                            open=True,
                        ))
                else:
                    step_text.value = "Error Generating Report"
                    page.update()
                    page.show_snack_bar(ft.SnackBar(
                        ft.Text(f"{analysis_result}", font_family='Roboto'),
                        open=True,
                    ))

            except Exception as e:
                step_text.value = "An unexpected error happened."
                page.update()
                page.show_snack_bar(ft.SnackBar(
                    ft.Text(f"An unexpected error happened while processing: {e}", font_family='Roboto'),
                    open=True,
                ))

            finally:
                is_processing = False
                submit_btn.disabled = False
                page.update()

    submit_btn = create_submit_button(lambda e: run_analysis(e), disabled=is_processing)

    def on_api_change(e):
        state.api_key = e.control.value

    page.add(
        ft.Column(
            [
                ft.Text(
                    "Financial Ratio Analyzer",
                    style=ft.TextStyle(size=32, weight=ft.FontWeight.BOLD),
                    color="#1E3B80"
                ),
                ft.Text(
                    "Upload a financial report (PDF) to extract and analyze financial ratios.",
                    color="grey", font_family="Roboto",
                    style=ft.TextStyle(size=14, weight=ft.FontWeight.W_300),
                ),
                create_upload_button(lambda e: open_file_picker(e)),
                file_display_text,
                ft.Container(api_key_field, padding=10),
                submit_btn,
                step_text,
                download_button,
            ],
            alignment=ft.CrossAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )
    page.update()

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

# financial_analyzer/core/pdf_processor.py
from typing import List
import os
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter


def load_and_extract_text_from_pdfs(pdf_paths: List[str], upload_dir: str) -> str:
    """Loads and extracts text from multiple PDFs from upload directory."""
    print("DEBUG: Starting load_and_extract_text_from_pdfs")
    all_text = []
    for pdf_path in pdf_paths:
        full_pdf_path = os.path.join(upload_dir, os.path.basename(pdf_path))
        print(f"DEBUG: Loading PDF: {full_pdf_path}")
        try:
            loader = PyPDFLoader(file_path=full_pdf_path)
            documents = loader.load()
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            all_text.extend([doc.page_content for doc in text_splitter.split_documents(documents)])
            print(f"DEBUG: Successfully loaded and split text from: {full_pdf_path}")
        except Exception as e:
             print(f"ERROR: Could not load or split text from {full_pdf_path}: {e}")
             continue

    if not all_text:
        print("DEBUG: No text extracted from any of the provided PDF documents.")
        return None

    combined_text = " ".join(all_text)
    print("DEBUG: Finished load_and_extract_text_from_pdfs")
    return combined_text

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

# financial_analyzer/core/data_extractor.py
from typing import TypedDict
from langchain.schema import HumanMessage
from core.llm import chat_model
import json
import re


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

# financial_analyzer/core/report_generator.py
from fpdf import FPDF
from langchain.schema import HumanMessage
from core.llm import chat_model
import json
from core.ratio_calculator import FinancialRatios
import os


def generate_pdf_report(ratios: FinancialRatios) -> str:
    """
    Generates PDF report with financial ratios and explanations
    :param ratios: Dictionary containing calculated ratios with specific structure
    :return: Path to generated PDF file
    """
    print("DEBUG: Starting generate_pdf_report tool")
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Header
        pdf.set_font("Arial", "B", 24)
        pdf.set_text_color(44, 62, 80)
        pdf.cell(0, 20, "Financial Ratio Analysis Report", ln=True, align="C")

        # Subtitle
        pdf.set_font("Arial", "I", 12)
        pdf.set_text_color(127, 140, 141)
        pdf.cell(0, 10, "Your friendly financial insights!", ln=True, align="C")
        pdf.ln(10)

        # Add ratios and explanations
        for ratio_name, ratio_value in ratios.items():
            # Card header
            pdf.set_fill_color(240, 240, 240)
            pdf.set_draw_color(200, 200, 200)
            pdf.rect(20, pdf.get_y(), 170, 10, style='FD')

            # Ratio name
            pdf.set_font("Arial", "B", 14)
            pdf.set_text_color(44, 62, 80)
            pdf.set_xy(25, pdf.get_y() + 2)
            pdf.cell(160, 6, f"{ratio_name.replace('_', ' ').title()}", ln=True)

            # Value section
            pdf.set_fill_color(249, 249, 249)
            pdf.rect(20, pdf.get_y(), 170, 15, style='FD')
            pdf.set_font("Arial", "B", 16)
            pdf.set_text_color(52, 152, 219)
            pdf.set_xy(25, pdf.get_y() + 4)
            pdf.cell(160, 6, f"{ratio_value:.2f}", ln=True)

            # Explanation section
            pdf.set_fill_color(255, 255, 255)
            pdf.rect(20, pdf.get_y(), 170, 20, style='FD')
            pdf.set_font("Arial", "", 10)
            pdf.set_text_color(100, 100, 100)
            pdf.set_xy(25, pdf.get_y() + 2)
            explanation = get_ratio_explanation(ratio_name, ratio_value, ratios)
            pdf.multi_cell(160, 5, explanation)

            pdf.ln(15)

        # Generate PDF in temporary location
        temp_path = "temp_report.pdf"
        pdf.output(temp_path)
        print(f"DEBUG: PDF Output Path: {temp_path}")
        print("DEBUG: Finished generate_pdf_report tool")
        return temp_path
    except Exception as e:
        print(f"ERROR: An error occurred inside `generate_pdf_report`: {e}")
        return None


def get_ratio_explanation(ratio_name: str, ratio_value: float, ratios: FinancialRatios) -> str:
    """
    Generates explanations for financial ratios using the LLM.
    """
    print(f"DEBUG: Starting get_ratio_explanation for {ratio_name}")
    prompt = f"""
        You are an expert financial analyst.

        Analyze the following financial ratio and provide a concise explanation of what it means for the company.
        Provide 2-3 sentences, comment on the strength or weakness and provide a recommendation in weakness situation of the ratio as well as provide additional context based on the other ratios provided.
        Use simple, understandable language. Be direct and clear. Do not include any introduction or conclusion text.

        Ratio Name: {ratio_name.replace('_', ' ').title()}
        Ratio Value: {ratio_value:.2f}
        All Ratios: {json.dumps(ratios, indent=4)}

        Explanation:
    """

    try:
        response = chat_model.invoke([HumanMessage(content=prompt)]).content
        print(f"DEBUG: LLM Explanation Response: {response}")
        return response.strip()
    except Exception as e:
        print(f"ERROR: Error generating ratio explanation: {e}")
        return "Could not generate an explanation for this ratio."
    finally:
        print(f"DEBUG: Finished get_ratio_explanation for {ratio_name}")

# financial_analyzer/config/app_config.py
import os
from dotenv import load_dotenv

load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")
flet_secret_key=os.getenv("FLET_SECRET_KEY")
