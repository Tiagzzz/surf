# Known Issues

Last updated: 2026-05-14 — Phase 7/7.1 app state reflected for final verification docs sync.

This file tracks user-facing issues, cleanup findings, and approval checkpoints that should remain visible to the team. It is for app-facing decisions, not internal planning history.

## UI polish closeout status

- The earlier button-font audit issue was addressed before this handoff-readiness work.
- Official-app review found three misses after the first closeout check: shared page-header typography not visibly applying, button/label text not using the intended font, and P2/P3 upload controls not working reliably.
- The adjustment patch keeps the native Streamlit file-uploader button visible/clickable in P2/P3, strengthens shared header CSS, and targets Streamlit inner button-label wrappers without broad page-global selectors.
- Follow-up common page-header visibility fix approved on 2026-05-12: `app.brain.page_header` now renders through the reliable Markdown/unsafe-HTML path when available. Approved scope is only My Classes, Class Hub, Dashboard, and Settings; P4/P5 keep their dedicated headers.
- Final Class Hub and Settings button-label fit/font fixes were approved on 2026-05-12.
- Final official-app human review is approved; no open user-facing known issues remain from that cycle.
- The closeout verification blocker found in the final UI-polish check was resolved locally by updating the dashboard wrapper test recorder to support `html(...)`; full `python -m pytest -q` passed before the final button tweak with 502 tests and 3 warnings; the final focused button checks passed with 74 tests and 3 warnings; `ruff check .` and scoped ruff also passed.

## Button-font audit inventory

Audit command run from the repo root:

```bash
rg -n 'st\.button|st\.form_submit_button|\[data-testid="stButton"\]|\[data-testid="stFormSubmitButton"\]|font-family: "JetBrains Mono"|font-family: "Fraunces"' app views tests
```

Decision rule: every visible user-facing Surf button label should use JetBrains Mono. Non-button body text, generated explanations, class names, lecture titles, MCQ option text overlays, chart labels, and generated review reasons must not be blindly converted.

| Bucket | Button surfaces checked | Classification | Follow-up |
|---|---|---|---|
| Topbar | Logo/Home and Settings icon buttons in `app/brain/topbar/__init__.py` | Compliant / not applicable: visible surfaces are icons; hidden Streamlit labels are not user-facing text. | None. |
| P1 Signup | `AI USE`, `START SURFING >`, AI-use dialog close path in `app/signup/signup_flow/__init__.py` | Compliant: scoped P1 button CSS uses JetBrains Mono. | None. |
| P2 My Classes | `ADD CLASS`, `DELETE CLASS`, `ENTER CLASS >`, Add Class form submit/discard, class-delete dialog buttons in `app/my_classes/class_list_render/__init__.py` | Approved after official-app review: selector also targets Streamlit inner button-label wrappers; factsheet uploader native button remains visible/clickable inside the large Dropbox zone. | None. |
| P3 Class Hub | `DASHBOARD >`, `TAKE MOCK >`, `ADD LECTURE`, `DELETE LECTURE`/`UNDO`, Attempt History toggle/review arrow, Add Lecture form buttons, lecture-delete dialog buttons in `app/class_/class_hub/__init__.py` | Approved after official-app review: selector also targets Streamlit inner button-label wrappers; lecture uploader native button remains visible/clickable inside the large Dropbox zone; final action-row labels are tightened/centered to fit. Hidden lecture-tile click targets are not visible labels; lecture titles stay non-button content. | None. |
| P4 Take Mock | recovery buttons, `KEEP ANSWERING`, finish/submit buttons, `SKIP`, `NEXT >`, MCQ option click targets in `app/mock_take/question_render/__init__.py` | Compliant after focused P4 button work. MCQ answer text is intentionally Fraunces overlay content, not a button-label typography target. | None. |
| P5 Review | recovery `BACK TO CLASS`, bottom `BACK TO CLASS`, `OPEN DASHBOARD` in `app/mock_review/results_render/__init__.py` | Compliant after focused P5 button work. Generated reasons are intentionally regular Fraunces and are not buttons. | None. |
| P6 Dashboard | stale/missing-class recovery `BACK TO MY CLASSES`; Study Next practice launch when rendered through shared Study Next section | Compliant after scoped `p6_dashboard_recovery` button-font CSS. Shared Study Next practice button is covered by the reused Study Next button CSS. | None. |
| P7 Settings | profile save, API key replacement, `AI USE`, reset open, reset dialog keep/delete, AI-use dialog close in `app/settings/__init__.py` | Approved after final correction: page and dialog button child-label wrappers use the JetBrains Mono contract for visible Settings labels. | None. |
| Dialogs/forms | P1/P2/P3/P4/P7 dialogs and P2/P3 forms | Compliant where currently styled; fixes stayed scoped by page/dialog key. | None. |

## Open known issues

No open user-facing known issues are currently recorded after the approved UI polish closeout and the P4/P5 documentation review pass.

Phase 7 and Phase 7.1 added the red `CUSTOM MOCK >` flow, P5
`Difficulty for you: X/100` badge, Claude difficulty metadata storage, and
local metadata/history personal scoring. No new user-facing blocker is recorded
from that work. Final package/demo key decisions remain approval-gated and are
not open app defects.

## Resolved issues

| ID | Surface | Original severity | Resolution | Status |
|---|---|---:|---|---|
| KI-2026-05-12-P6-RECOVERY-BUTTON-FONT | P6 Dashboard stale/missing-class recovery button `BACK TO MY CLASSES` (`app/dashboard/dashboard_flow/__init__.py`, key `p6_back_to_my_classes`) | Low | Addressed with scoped CSS under `p6_dashboard_recovery` / `p6_back_to_my_classes`; focused dashboard/settings tests passed in closeout. | Resolved and approved. |
| KI-2026-05-12-OFFICIAL-APP-ADJUSTMENTS | P2/P3/P7/shared header official app review | Medium | Strengthened shared page-header typography CSS, targeted inner Streamlit button-label wrappers, restored visible/clickable native uploader buttons inside the P2/P3 Dropbox zones, fixed common page-header visibility by rendering the shared helper through Markdown/unsafe HTML, and tightened/centered remaining P3/P7 button labels. | Resolved and approved on 2026-05-12. |

## Documentation approval log

| ID | Surface | Approval need | Status | Notes |
|---|---|---|---|---|
| SIGNUP-DOCS-APPROVAL | P1 signup comments, file sidecar, page sidecar, bucket doc, and impact-register mapping | Review whether this adjusted sample is natural, teachable, safe, and worth copying to later documentation cleanup | Approved by product owner on 2026-05-13 | No signup behavior issue found. The approved sample requires precise block-level comments, sidecar code snippets, easier code walkthroughs tied to actual code, and explicit external tools/functions lists. Later documentation work should copy this adjusted pattern. |
| CROSS-CUTTING-DOCS-REVIEW | `.gitignore`, `README.md`, and `docs/team/` educational docs | Review whether the team docs are teachable, neutral, safe, and ready to guide later handoff work after Phase 7/7.1 alignment | Pending product-owner approval | Docs/config only. Phase 8 Plan 08-02 refreshes README/team docs for the current app state; it does not run external notebook sync, live API calls, live database mutation, final package, final demo database/key, or contribution matrix work. |
| MY-CLASSES-DOCS-REVIEW | P2 My Classes comments, bucket/file sidecars, `views/my_classes.md`, and impact-register mapping | Review whether the P2 docs are teachable, neutral, safe, and behavior-preserving before Class Hub review starts | Pending product-owner approval | Behavior-preserving documentation cleanup only. No class editing/archive scope, final teacher package, final demo database/key, external notebook sync, live database inspection/mutation, or model-analysis changes were made. |
| CLASS-HUB-DOCS-REVIEW | P3 Class Hub comments, class bucket/file sidecars, `views/class_view.md`, and impact-register mapping | Review whether the P3 docs are teachable, neutral, safe, and behavior-preserving before the next documentation area starts | Pending product-owner approval | Behavior-preserving documentation cleanup only. No lecture-ingestion behavior change, mock/practice launch persistence change, broad lecture management scope, final teacher package, final demo database/key, external notebook sync, live database inspection/mutation, or model-analysis changes were made. |
| MOCK-ATTEMPT-REVIEW-DOCS-REVIEW | P4/P5 take/review comments, bucket/file sidecars, `views/take_mock_exam.md`, `views/review_mock_exam.md`, and impact-register mapping | Review whether the P4/P5 docs are teachable, neutral, safe, and behavior-preserving before dashboard cleanup starts | Pending product-owner approval | Behavior-preserving documentation cleanup only. Verification passed for scoped lint, focused attempt/review tests, internal-voice grep, deferred-feature grep, and whitespace diff check. No grading, transaction, review display, dashboard analytics, final teacher package, final demo database/key, external notebook sync, live database inspection/mutation, or model-analysis changes were made. |
| DASHBOARD-DOCS-REVIEW | P6 Dashboard comments, bucket/file sidecars, `views/dashboard.md`, and impact-register mapping | Review whether the Dashboard docs are teachable, neutral, safe, and behavior-preserving before ML/entrypoint cleanup starts | Approved by product owner on 2026-05-13 | Behavior-preserving documentation cleanup only. Verification passed for scoped lint, compile checks, sidecar-template grep, internal-voice grep, and focused dashboard tests. No dashboard analytics behavior, final package, final demo database/key, external notebook sync, live database inspection/mutation, or model-analysis wiring was changed. |
| ML-ENTRYPOINT-DOCS-REVIEW | `app/ml/` docs, `streamlit_app.py` comments, `streamlit_app.md`, route-sidecar consistency, and impact-register mapping | Review whether the ML preservation and router docs are teachable, neutral, safe, and behavior-preserving before the final readiness/deletion gate starts | Approved by product owner on 2026-05-13 | This approval covered the pre-Phase-7 documentation/comment cleanup. After Phase 7/7.1, `app/ml/personal_difficulty/` is live for Custom Mock and P5 personal difficulty; empty future scaffold folders were removed during Phase 7.1 closeout. No model artifact, live database action, external notebook sync, final package, or demo DB/key action is approved by this row. |
