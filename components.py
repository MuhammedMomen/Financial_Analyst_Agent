import flet as ft

# Component for API Key Field
def create_api_key_field(api_key, on_change):
    return ft.TextField(
        label="Enter your Google API key (optional)",
        value=api_key,
        password=True,  # masking api key for security reasons
        can_reveal_password=True,  # add ability to check unmasked api
        width=600,
        on_change=on_change,
    )


# Component for File Display Text
def create_file_display_text():
    return ft.Text(
        "No PDF file(s) selected.",
        font_family="Roboto",
        color="grey",
    )


# Component for Upload Button
def create_upload_button(on_click):
    return ft.Container(
        ft.OutlinedButton(
            "Upload PDF(s)",
            on_click=on_click,
            icon=ft.icons.UPLOAD_FILE,
            width=600,
        ),
        padding=10
    )

# Component for Progress Text
def create_step_text():
    return ft.Text("", font_family="Roboto", color="green")


# Component for submit button
def create_submit_button(on_click, disabled=False):
    return ft.ElevatedButton(
          text="Analyze Financials",
            on_click=on_click,
            width=600,
            disabled=disabled
           )