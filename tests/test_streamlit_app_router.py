"""Tests for Surf's top-level Streamlit router behavior."""
from __future__ import annotations

import importlib
import sys

import pytest

from app.settings import _render_reset_dialog


class _SwitchPage(Exception):
    """Raised by the fake Streamlit module when navigation interrupts."""


class _Navigation:
    def __init__(self, calls: list):
        self._calls = calls

    def run(self) -> None:
        self._calls.append(("run",))


class _FakeStreamlit:
    def __init__(self, *, session_state: dict | None = None):
        self.session_state = session_state if session_state is not None else {}
        self.calls: list = []

    def Page(self, path: str, *, title: str, default: bool = False):  # noqa: N802
        page = {"path": path, "title": title, "default": default}
        self.calls.append(("Page", page))
        return page

    def navigation(self, pages: list):
        self.calls.append(("navigation", pages))
        return _Navigation(self.calls)

    def switch_page(self, path: str) -> None:
        self.calls.append(("switch_page", path))
        raise _SwitchPage(path)


def _load_router(monkeypatch, *, authenticated: bool, session_state: dict | None = None):
    fake_st = _FakeStreamlit(session_state=session_state)
    monkeypatch.setitem(sys.modules, "streamlit", fake_st)

    import app.brain.session as session

    monkeypatch.setattr(session, "is_authenticated", lambda: authenticated)
    sys.modules.pop("streamlit_app", None)
    try:
        module = importlib.import_module("streamlit_app")
    except _SwitchPage:
        module = sys.modules.get("streamlit_app")
    return fake_st, module


def test_authenticated_fresh_browser_session_redirects_to_my_classes(monkeypatch):
    fake_st, _module = _load_router(monkeypatch, authenticated=True)

    assert ("switch_page", "views/my_classes.py") in fake_st.calls
    assert fake_st.session_state["_surf_authenticated_home_redirect_done"] is True
    assert ("run",) not in fake_st.calls


def test_authenticated_existing_session_keeps_in_app_navigation(monkeypatch):
    session_state = {"_surf_authenticated_home_redirect_done": True}
    fake_st, _module = _load_router(
        monkeypatch,
        authenticated=True,
        session_state=session_state,
    )

    assert ("switch_page", "views/my_classes.py") not in fake_st.calls
    assert ("run",) in fake_st.calls


def test_unauthenticated_router_runs_signup_only(monkeypatch):
    fake_st, _module = _load_router(monkeypatch, authenticated=False)

    navigation_calls = [call for call in fake_st.calls if call[0] == "navigation"]
    assert len(navigation_calls) == 1
    pages = navigation_calls[0][1]
    assert pages == [{"path": "views/signup.py", "title": "Sign Up", "default": True}]
    assert ("switch_page", "views/my_classes.py") not in fake_st.calls
    assert ("run",) in fake_st.calls


class _Container:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class _ResetDialogStreamlit:
    def __init__(self):
        self.session_state = {"stale": "value"}
        self.calls: list = []

    def dialog(self, _title):
        def _decorator(fn):
            return fn

        return _decorator

    def html(self, content: str) -> None:
        self.calls.append(("html", content))

    def text_input(self, *_args, **_kwargs) -> str:
        return "DELETE"

    def columns(self, *_args, **_kwargs):
        return [_Container(), _Container()]

    def button(self, _label, *, key: str, **_kwargs) -> bool:
        return key == "p7_reset_confirm"

    def toast(self, message: str) -> None:
        self.calls.append(("toast", message))

    def rerun(self) -> None:
        self.calls.append(("rerun",))
        raise RuntimeError("rerun")

    def switch_page(self, path: str) -> None:
        self.calls.append(("switch_page", path))


def test_confirmed_reset_clears_state_and_reruns_router(monkeypatch):
    import app.settings as settings

    fake_st = _ResetDialogStreamlit()
    reset_calls: list = []
    monkeypatch.setattr(settings, "st", fake_st)

    with pytest.raises(RuntimeError, match="rerun"):
        _render_reset_dialog(reset_fn=lambda: reset_calls.append("reset"))

    assert reset_calls == ["reset"]
    assert fake_st.session_state == {}
    assert ("toast", "Local data deleted.") in fake_st.calls
    assert ("rerun",) in fake_st.calls
    assert not any(call[0] == "switch_page" for call in fake_st.calls)
