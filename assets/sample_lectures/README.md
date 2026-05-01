# sample_lectures

`sample_lecture.pdf` is a 3-page placeholder used by `tests/test_smoke.py` to drive the Phase 1 end-to-end ingestion test (`test_ingestion_end_to_end_against_fresh_sqlite`). It is **not** a real lecture — Phase 5 (sample-data polish) replaces it with a real HSG slide deck.

## Regenerate

`reportlab` is a generation-time dep only (not a runtime dep). One-shot regeneration:

```bash
pip install reportlab
python -c "
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from pathlib import Path
out = Path('assets/sample_lectures/sample_lecture.pdf')
out.parent.mkdir(parents=True, exist_ok=True)
c = canvas.Canvas(str(out), pagesize=A4)
for i, body in enumerate([
    'Slide 1: Course intro and agenda.',
    'Slide 2: Core concept - supply and demand curves.',
    'Slide 3: Source list and references.',
], start=1):
    c.setFont('Helvetica-Bold', 24); c.drawString(100, 700, f'Page {i}')
    c.setFont('Helvetica', 14); c.drawString(100, 660, body)
    c.showPage()
c.save()
"
```
