#Jordon Draper
#U1600919
#Final Project

import flet as ft


def main(page: ft.Page) -> None:
    page.title = "Culture Quest"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    page.add(
        ft.Text("Culture Quest", size=32, weight=ft.FontWeight.BOLD),
        ft.Text("A cultural travel and language companion"),
    )

if __name__ == "__main__":
    ft.run(main)