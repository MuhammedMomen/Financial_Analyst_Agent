# financial_analyzer/ui/main.py
import flet as ft
import os
from typing import List
import shutil
from core.agent import process_financial_analysis
from config.app_config import google_api_key,flet_secret_key
from ui.components import create_api_key_field, create_file_display_text, create_upload_button, create_step_text, create_submit_button
from flet import FilePickerUploadFile, FilePickerResultEvent


def main(page: ft.Page):
    page.title = "Financial Statement Analysis App"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.window_width = 700
    page.window_height = 800
    page.theme = ft.theme.Theme(color_scheme_seed='blue')  # use seed theme color of blue

    # Create upload directory in the root directory
    upload_dir = "upload_dir"  # Directory to store files during web execution
    os.makedirs(upload_dir, exist_ok=True)

    # Variables for storing state
    uploaded_files = []
    api_key = google_api_key if google_api_key else ''
    is_processing = False

    # Create a shared state for accessing `api_key`  from local to use on nested call back.
    state = type('state', (object,), {
        "api_key": api_key
    })()

     # --- FLET UI Elements ---
    def on_upload_callback(e):
        if e.error:
            print(f"ERROR: Upload error for file: {e.file_name}: {e.error}")
            page.show_snack_bar(ft.SnackBar(ft.Text(f"Error uploading file: {e.file_name}, Error:{e.error}", font_family='Roboto'), open=True))
        
        else:
             print(f"DEBUG: File {e.file_name} uploaded successfully.")

    # File picker
    file_picker = ft.FilePicker(
        on_result=lambda e: on_files_selected(e),
        on_upload=on_upload_callback
    )
    page.overlay.append(file_picker)

    # File Input Display
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
            # Prepare the file for upload using page.get_upload_url to let Flet handle the process.
            upload_url = page.get_upload_url(file.name, 600) # 600 is arbitrary number for timeout
            upload_list.append(
                    FilePickerUploadFile(
                    file.name,
                    upload_url=upload_url,
                )
            )
            # store full upload path on `uploaded_files`.
            uploaded_files.append(file.name)

        file_picker.upload(upload_list)

        file_names = [file.name for file in e.files]
        update_file_display(file_names)


    # API key text field
    api_key_field = create_api_key_field(api_key, lambda e: on_api_change(e))


    # Step progress text
    step_text = create_step_text()

    # Action button (Analyze or Processing animation)
    def run_analysis(e):
        # Use shared api_key state  to access value set via api_field and shared across page
        if not state.api_key:
            page.show_snack_bar(ft.SnackBar(
                ft.Text("Please provide the api key", font_family='Roboto'),
                open=True,
            )
            )
        elif not uploaded_files:
            page.show_snack_bar(ft.SnackBar(
                ft.Text("Please upload at least 1 PDF file.", font_family='Roboto'),
                open=True,
            )
            )
        else:
            # start spinning icon to prevent multiple action executions

            page.update()

            try:

                step_text.value = "Extracting Data..."
                page.update()
                # Correct the call here to use full path of each uploaded file in  `process_financial_analysis` function.
                full_paths=[os.path.join(upload_dir, file) for file in uploaded_files ]
                analysis_result = process_financial_analysis(full_paths, state.api_key, upload_dir)

                if os.path.exists(analysis_result):  # if result is path to download report
                    step_text.value = "Report Generated Successfully"  # updated success state.
                    page.update()
                    page.launch_url(analysis_result)

                else:  # if no report returned or is a `str` from error method return it is handle via ui via this `snack bar`.
                    step_text.value = "Error Generating Report"  # update error state.
                    page.update()
                    page.show_snack_bar(ft.SnackBar(
                        ft.Text(f"{analysis_result}", font_family='Roboto'),
                        open=True,
                    )
                    )

            except Exception as e:  # any other exception that we catch
                step_text.value = "An unexpected error happened."  # update error state
                page.update()
                page.show_snack_bar(ft.SnackBar(
                    ft.Text(f"An unexpected error happened while processing: {e}", font_family='Roboto'),
                    open=True,
                )
                )

            finally:
                # stop spinning icon after processing completed
                is_processing = False
                submit_btn.disabled = False

                page.update()

    submit_btn = create_submit_button(lambda e: run_analysis(e), disabled=is_processing)

    def on_api_change(e):
        # update local variable of shared object `state` to store data in page context and re access later
        state.api_key = e.control.value

    #  main layout
    page.add(
        ft.Column(
            [

                ft.Text(
                    "Financial Ratio Analyzer",
                    style=ft.TextStyle(size=32, weight=ft.FontWeight.BOLD),
                    color="#1E3B80"
                ),  # title
                ft.Text(
                    "Upload a financial report (PDF) to extract and analyze financial ratios.",
                    color="grey", font_family="Roboto",
                    style=ft.TextStyle(size=14, weight=ft.FontWeight.W_300),
                ),  # Sub title
                create_upload_button(lambda e: open_file_picker(e)),
                file_display_text,  # Display File text
                ft.Container(api_key_field, padding=10),  # text field with google api key
                submit_btn,
                step_text,
            ],

            alignment=ft.CrossAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,

        )
    )
    page.update()