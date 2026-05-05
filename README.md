# Surf — Adaptive HSG Study Companion

Personalized exam-prep app for HSG students. Upload your class factsheet + lecture PDFs; get auto-generated mock exams from your own course materials, ranked by ML-scored difficulty and adapted to your weak spots.

- **Course:** Computer Science for Business (FCS-BWL), HSG FS 2026
- **Team:** Tiago, Nikita, Constance, Juliette, Jonas
- **Stack:** Python · Streamlit · SQLite · Anthropic Claude API

---

## Quick start (for graders)

Tested on macOS / Linux / Windows. Python **3.11** recommended.

```bash
# 1. Clone
git clone https://github.com/Tiagzzz/surf.git
cd surf

# 2. Set up Python environment
python -m venv .venv
source .venv/bin/activate         # macOS / Linux
# .venv\Scripts\activate          # Windows PowerShell

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
streamlit run streamlit_app.py
```

Open `http://localhost:8501` in your browser. On first launch you will be asked for an Anthropic API key (get one at <https://console.anthropic.com>). The key is stored locally in `~/.surf/user.sqlite` — nothing leaves your machine except API calls to Claude.

---

## Project structure

The codebase is organised into **10 buckets**, with **one sub-folder per pipeline** inside each bucket. Internal planning and handoff documents are intentionally kept local-only and are not part of the GitHub repo.

```
surf/
├── streamlit_app.py            # Entry — auth router (st.navigation)
├── views/                      # 7 thin page files (1 signup + 6 authenticated), one per Streamlit page (renamed from pages/ to avoid Streamlit auto-magic collision)
│   ├── signup.py               # P1
│   ├── my_classes.py           # P2 (Home)
│   ├── class_view.py           # P3 (renamed from `class` — Python keyword)
│   ├── take_mock_exam.py       # P4
│   ├── review_mock_exam.py     # P5
│   ├── dashboard.py            # P6
│   └── settings.py             # P7
├── app/                        # 10 buckets — implementation lives here
│   ├── brain/                  # Tier 1 — shared infrastructure
│   ├── db/                     # Tier 1 — SQLite schema + queries
│   ├── ml/                     # Tier 1 — 6-criteria difficulty model
│   ├── signup/                 # Tier 2 — P1
│   ├── my_classes/             # Tier 2 — P2
│   ├── class_/                 # Tier 2 — P3
│   ├── mock_take/              # Tier 2 — P4
│   ├── mock_review/            # Tier 2 — P5
│   ├── dashboard/              # Tier 2 — P6
│   └── settings/               # Tier 2 — P7
├── tests/                      # pytest tests, mirrors app/
├── previews/                   # local visual preview sandboxes when included for a task
└── assets/                     # screenshots, demo PDFs, video assets
```

---

## Repository hygiene

Internal planning, handoff, course-download, and agent-instruction files are intentionally excluded from GitHub. The public repo should contain runnable app code, tests, sanitized assets, and this self-contained README only. Local SQLite databases, API keys, Canvas downloads, and agent worktrees must not be committed.

---

## License

MIT — see [LICENSE](LICENSE).
