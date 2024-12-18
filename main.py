# financial_analyzer/main.py
import flet as ft
import os
from ui import main as ui_main
from config.app_config import flet_secret_key


if __name__ == "__main__":
    # Set FLET_SECRET_KEY as environment variable
    os.environ["FLET_SECRET_KEY"] = flet_secret_key

    ft.app(target=ui_main.main, view=ft.AppView.WEB_BROWSER, assets_dir="assets",upload_dir="upload_dir")
