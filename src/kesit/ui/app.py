"""Kotline desktop application entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> None:
    from kesit.ui import i18n

    parser = argparse.ArgumentParser(description=i18n.t("cli.description"))
    parser.add_argument(
        "--demo",
        action="store_true",
        help=i18n.t("cli.demo_help"),
    )
    parser.add_argument(
        "--project",
        type=Path,
        metavar="PATH",
        help=i18n.t("cli.project_help"),
    )
    parser.add_argument(
        "project_file",
        nargs="?",
        type=Path,
        help=i18n.t("cli.project_file_help"),
    )
    args = parser.parse_args()

    project_path = args.project or args.project_file

    try:
        import customtkinter as ctk
    except ImportError as exc:
        print(i18n.t("cli.ctk_required"), file=sys.stderr)
        print(i18n.t("cli.ctk_install"), file=sys.stderr)
        raise SystemExit(1) from exc

    from kesit.ui.main_window import MainWindow

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    root_dir = Path(__file__).resolve().parents[3]
    app = MainWindow(root_dir=root_dir, auto_demo=args.demo and project_path is None)
    if project_path is not None:
        app.after(200, lambda: app.load_project_into_ui(project_path.resolve()))
    app.mainloop()


if __name__ == "__main__":
    main()
