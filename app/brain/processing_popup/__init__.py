"""Shared Surf upload-processing popup."""
from __future__ import annotations

import base64
from functools import lru_cache
from html import escape
from pathlib import Path
from typing import Any, Literal

_REPO_ROOT = Path(__file__).resolve().parents[3]
_VIDEO_PATH = _REPO_ROOT / "assets" / "media" / "surfer-processing-loop.mp4"

PopupState = Literal["processing", "done"]


@lru_cache(maxsize=1)
def _video_data_uri() -> str:
    encoded = base64.b64encode(_VIDEO_PATH.read_bytes()).decode("ascii")
    return f"data:video/mp4;base64,{encoded}"


def build_processing_popup_html(
    *,
    state: PopupState,
    video_data_uri: str | None = None,
) -> str:
    """Return the two-state upload-processing popup HTML."""
    if state == "processing":
        title = "Your file is being processed"
        subtitle = "THE APP WILL RELOAD ONCE IT IS DONE"
        status_text = "processing ..."
        status_class = "is-processing"
    elif state == "done":
        title = "Your file is ready"
        subtitle = "REFRESHING PAGE TO CONTINUE SURFING!"
        status_text = "Done!"
        status_class = "is-done"
    else:
        raise ValueError(f"Unknown processing popup state: {state!r}")

    data_uri = video_data_uri if video_data_uri is not None else _video_data_uri()
    video_markup = (
        '<video class="surf-processing-video" autoplay muted loop playsinline '
        'preload="auto" aria-label="Surf processing animation">'
        f'<source src="{escape(data_uri, quote=True)}" type="video/mp4">'
        "</video>"
    )

    return f"""
<style>
  .surf-processing-backdrop {{
    align-items: center;
    background: rgba(23, 21, 17, 0.34);
    display: flex;
    inset: 0;
    justify-content: center;
    position: fixed;
    z-index: 999999;
  }}
  .surf-processing-card {{
    background: rgba(253, 246, 238, 1);
    border: 2px solid #1f1c18;
    border-radius: 8px;
    box-shadow: 8px 8px 0 #11100d;
    box-sizing: border-box;
    color: #25211c;
    height: min(835px, calc(100vh - 48px));
    max-height: 835px;
    max-width: calc(100vw - 48px);
    overflow: hidden;
    padding: 30px 30px 28px;
    position: relative;
    width: min(960px, calc(100vw - 48px));
  }}
  .surf-processing-title {{
    color: #25211c;
    font-family: "Fraunces", Georgia, serif;
    font-size: clamp(34px, 4.6vw, 46px);
    font-style: italic;
    font-weight: 700;
    letter-spacing: -0.03em;
    line-height: 0.98;
    margin: 0 0 16px;
  }}
  .surf-processing-subtitle {{
    color: #756e64;
    font-family: "JetBrains Mono", ui-monospace, monospace;
    font-size: clamp(14px, 2.1vw, 20px);
    font-weight: 500;
    letter-spacing: 0.33em;
    line-height: 1.25;
    margin: 0;
    text-transform: uppercase;
  }}
  .surf-processing-video-wrap {{
    align-items: center;
    display: flex;
    inset: 150px 90px 120px;
    justify-content: center;
    position: absolute;
  }}
  .surf-processing-video {{
    display: block;
    height: auto;
    max-height: 100%;
    max-width: 100%;
    object-fit: contain;
    width: min(620px, 100%);
  }}
  .surf-processing-status {{
    align-items: center;
    bottom: 32px;
    color: #756e64;
    display: flex;
    font-family: "JetBrains Mono", ui-monospace, monospace;
    font-size: 22px;
    font-weight: 400;
    gap: 16px;
    left: 30px;
    letter-spacing: 0.14em;
    line-height: 1;
    position: absolute;
  }}
  .surf-processing-dot {{
    border-radius: 999px;
    display: inline-block;
    height: 16px;
    width: 16px;
  }}
  .surf-processing-status.is-processing .surf-processing-dot {{
    background: #d53821;
  }}
  .surf-processing-status.is-done .surf-processing-dot {{
    background: #2e7a4d;
  }}
</style>
<div class="surf-processing-backdrop" role="status" aria-live="polite">
  <section class="surf-processing-card" aria-label="{escape(title, quote=True)}">
    <h2 class="surf-processing-title">{escape(title)}</h2>
    <p class="surf-processing-subtitle">{escape(subtitle)}</p>
    <div class="surf-processing-video-wrap">{video_markup}</div>
    <div class="surf-processing-status {status_class}">
      <span class="surf-processing-dot" aria-hidden="true"></span>
      <span>{escape(status_text)}</span>
    </div>
  </section>
</div>
"""


def show_processing_popup(
    placeholder: Any,
    *,
    state: PopupState,
) -> None:
    """Render the popup into a Streamlit placeholder-like object."""
    html = build_processing_popup_html(state=state)
    if hasattr(placeholder, "markdown"):
        placeholder.markdown(html, unsafe_allow_html=True)
    else:
        placeholder.html(html)
