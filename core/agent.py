import os
from typing import List
from langchain.schema import HumanMessage
from langgraph.prebuilt import create_react_agent
from core.llm import chat_model
from core.tools import get_financial_data, calculate_ratios_tool, generate_pdf_report_tool


# Define the Prompt
system_prompt = """
You are a financial analysis agent. Follow these steps:
1. Get financial data from the provided PDF files using get_financial_data tool.
2. Calculate financial ratios using calculate_ratios tool.
3. Generate PDF report using generate_pdf_report tool.
4. If the report is successfully generated, provide the path to the generated report. Otherwise, return an error message.
"""

# Create Agent
tools = [get_financial_data, calculate_ratios_tool, generate_pdf_report_tool]
agent = create_react_agent(chat_model, tools, state_modifier=system_prompt)

def process_financial_analysis(pdf_paths: List[str], api_key_from_ui:str, upload_dir: str):
    # Convert request to LangChain messages
    
    # update chat model with current key before action happens
    chat_model.google_api_key=api_key_from_ui
    
    print("DEBUG: Starting process_financial_analysis")
    history = [HumanMessage(content=f"Please analyze the financial statements from the following PDF files: {pdf_paths}")]
    
    # Invoke the agent
    try:
      response = agent.invoke({"messages": history, "pdf_paths": pdf_paths, "upload_dir": upload_dir})['messages'][-1].content
      print("DEBUG: Finished process_financial_analysis")
       # Check if the response is not empty and is not null, or exception if pdf creation is successful 
      if response and isinstance(response,str) and os.path.exists(response): # proper check on `result` for valid state as correct path of result download PDF 
          return response #returns valid value to ui download
      else: # if pdf error happens or empty, it goes here and displays a general error message on ui.
            return "I encountered an error while generating the PDF report. The ratios were calculated but the report was not generated."
      
    except Exception as e:
      print(f"ERROR: An error occurred during agent invocation: {e}")
      return f"I encountered an error when trying to process the PDF file. Please check the PDF content, its format and file integrity or provide the financial data manually: {e}"