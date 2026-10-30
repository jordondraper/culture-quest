# Jordon Draper
# U1600919
# Final Project

"""CultureQuest: start the app.

Run with the virtual environment active:  python main.py
"""

from pathlib import Path

import flet as ft
from dotenv import load_dotenv

from src.loaders import load_app_data
from src.state import AppState
from ui import messages, theme
from ui.shell import AppShell

ASSETS_DIR = Path(__file__).resolve().parent / "assets"  # bundled fonts


def main(page: ft.Page) -> None:
    page.title = messages.APP_NAME
    theme.apply_theme(page)
    shell = AppShell(page, AppState(loader=load_app_data))
    shell.load()


if __name__ == "__main__":
    load_dotenv()  # reads REST_COUNTRIES_API_KEY from .env
    ft.run(main, assets_dir=str(ASSETS_DIR))
