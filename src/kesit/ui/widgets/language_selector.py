"""Language selector for the main toolbar."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from kesit.ui import i18n, theme

LOCALE_CODES = ("en", "tr")


class LanguageSelector(ctk.CTkFrame):
    def __init__(
        self,
        master,
        locale: str = "en",
        on_change: Callable[[str], None] | None = None,
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._on_change = on_change
        self._locale = locale if locale in LOCALE_CODES else "en"

        self._label = ctk.CTkLabel(
            self, text=i18n.t("params.language"), font=theme.FONT_UI,
            text_color=theme.TEXT_MUTED,
        )
        self._label.pack(side="left", padx=(0, 6))

        self._menu = ctk.CTkOptionMenu(
            self,
            values=[self._display(code) for code in LOCALE_CODES],
            width=110,
            command=self._on_selected,
        )
        self._menu.set(self._display(self._locale))
        self._menu.pack(side="left")

    @staticmethod
    def _display(code: str) -> str:
        return i18n.t(f"locale.{code}")

    @staticmethod
    def _code_from_display(label: str) -> str:
        for code in LOCALE_CODES:
            if LanguageSelector._display(code) == label:
                return code
        return "en"

    def _on_selected(self, display: str) -> None:
        code = self._code_from_display(display)
        self._locale = code
        if self._on_change:
            self._on_change(code)

    def set_locale(self, code: str) -> None:
        self._locale = code if code in LOCALE_CODES else "en"
        self._menu.configure(values=[self._display(c) for c in LOCALE_CODES])
        self._menu.set(self._display(self._locale))

    def refresh_locale(self) -> None:
        self._label.configure(text=i18n.t("params.language"))
        self._menu.configure(values=[self._display(c) for c in LOCALE_CODES])
        self._menu.set(self._display(self._locale))
