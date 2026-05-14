"""Source-level contract tests for the Phase 7 Custom Mock button on P3."""
from __future__ import annotations

import inspect
import re

from app.class_ import class_hub


def _source() -> str:
    return inspect.getsource(class_hub)


def test_custom_mock_button_copy_and_css_contract():
    src = _source()
    # Locked label.
    assert "CUSTOM MOCK >" in src
    assert "How does it work? learn more" in src
    assert "hit me with the hard ones" in src
    assert "Nothing new is generated !" in src
    # CSS hook for the button container, copying Dashboard dimensions.
    assert ".st-key-p3_custom_mock_button button" in src
    assert ".st-key-p3_custom_mock_learn_more button" in src
    assert ".st-key-p3_custom_mock_help_card" in src
    # Red fill — uses the existing Surf accent token.
    assert "var(--surf-accent)" in src
    # Same stamped height / shadow rhythm as Dashboard.
    assert "height: 64px" in src
    assert "box-shadow: 4px 4px 0 var(--surf-shadow)" in src


def test_custom_mock_button_renders_directly_under_dashboard():
    # Inspect the layout renderer specifically — the call order there is
    # what determines visual placement.
    layout_src = inspect.getsource(class_hub._default_layout_renderer)
    dashboard_idx = layout_src.index(
        "_render_dashboard_button(switch_page_fn=switch_page_fn)"
    )
    custom_idx = layout_src.index("_render_custom_mock_button(")
    explainer_idx = layout_src.index("_render_custom_mock_explainer()")
    build_mock_idx = layout_src.index('st.container(key="p3_build_mock_card")')
    assert dashboard_idx < custom_idx < explainer_idx < build_mock_idx
    # No other p3_ widget squeezed between Dashboard render and Custom
    # Mock render.
    between = layout_src[dashboard_idx:custom_idx]
    other_p3_keys = re.findall(r'key="p3_[a-z_]+', between)
    assert other_p3_keys == [], (
        f"unexpected widget between Dashboard and Custom Mock: {other_p3_keys}"
    )


def test_custom_mock_button_does_not_replace_take_mock_or_study_next():
    src = _source()
    # Standard mock launch wiring remains intact.
    assert "TAKE_MOCK_LABEL" in src
    assert "_render_take_mock_button" in src
    assert "launch_mock_standard" in src
    # Study Next wiring remains intact.
    assert "study_next_launch_fn" in src
    assert "launch_study_next_practice" in src
    # Custom launch is wired as a separate injected helper.
    assert "custom_launch_fn" in src
    assert "launch_mock_custom" in src
    # Make sure we haven't deleted the dashboard wiring either.
    assert "DASHBOARD_LABEL" in src
    assert "_render_dashboard_button" in src


def test_custom_mock_button_routes_to_take_mock_view():
    helper = inspect.getsource(class_hub._render_custom_mock_button)
    # Routes to the existing P4 path.
    assert "TAKE_MOCK_VIEW_PATH" in helper
    # And shows a toast on the empty-pool path.
    assert "CUSTOM_MOCK_EMPTY_TOAST" in helper


def test_custom_mock_explainer_is_text_only_and_does_not_call_launch():
    helper = inspect.getsource(class_hub._render_custom_mock_explainer)
    assert "CUSTOM_MOCK_HELP_OPEN_KEY" in helper
    assert "CUSTOM_MOCK_HELP_BODY" in helper
    assert "p3_custom_mock_learn_more_action" in helper
    assert "custom_launch_fn" not in helper
    assert "launch_mock_custom" not in helper
    assert "TAKE_MOCK_VIEW_PATH" not in helper


def test_custom_mock_helper_does_not_call_db_directly():
    helper = inspect.getsource(class_hub._render_custom_mock_button)
    # The renderer only touches Streamlit + injected launch function.
    assert "from app.db" not in helper
    assert "claude_client" not in helper
    assert "nlm" not in helper
    assert "requests" not in helper
    assert "httpx" not in helper


def test_custom_mock_export_surface():
    assert "CUSTOM_MOCK_LABEL" in class_hub.__all__
    assert "CUSTOM_MOCK_EMPTY_TOAST" in class_hub.__all__
    assert "CUSTOM_MOCK_HELP_LABEL" in class_hub.__all__
    assert "CUSTOM_MOCK_HELP_BODY" in class_hub.__all__
    assert class_hub.CUSTOM_MOCK_LABEL == "CUSTOM MOCK >"
