from app.brain.processing_popup import build_processing_popup_html


def test_processing_popup_autoplays_and_loops_video():
    html = build_processing_popup_html(
        state="processing",
        video_data_uri="data:video/mp4;base64,abc",
    )

    assert "Your file is being processed" in html
    assert "THE APP WILL RELOAD ONCE IT IS DONE" in html
    assert "processing ..." in html
    assert "<video" in html
    assert "autoplay" in html
    assert "muted" in html
    assert "loop" in html
    assert "playsinline" in html
    assert "background: rgba(253, 246, 238, 1);" in html


def test_processing_popup_has_done_state_copy():
    html = build_processing_popup_html(
        state="done",
        video_data_uri="data:video/mp4;base64,abc",
    )

    assert "Your file is ready" in html
    assert "REFRESHING PAGE TO CONTINUE SURFING!" in html
    assert "Done!" in html
    assert "is-done" in html
