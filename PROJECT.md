---
kind: python-desktop
created: 2026-10-16
status: planned
---
# exam-planner

## Goal
- University course project #60 (Python): exam preparation planner.
- The user enters exams (name, date) and topics (name, difficulty 1-5). The program spreads topics over
  the days left and rebuilds the plan when the user falls behind. Result is shown as a workload calendar.
- Success: a student can plan 3+ exams in the window, mark topics done/missed, and see the plan update.

## Users
- One student, one machine, Russian UI. No accounts, no network.

## Constraints (from the assignment)
- Only course material: error handling, dicts, OOP (required), tkinter visualization (4th criterion),
  pytest, git, code style, debugging, classes, advanced Python features. No unrelated frameworks.
- Storage: CSV files (no database).
- Dependencies: standard library only (tkinter, csv, datetime, dataclasses). Dev-only: pytest.
- UI: tkinter with ttk and a tidy minimal look (consistent spacing, colors, readable fonts).
- Code, comments, commits in English; UI text in Russian.

## Scope
- In:
  - Classes `Exam`, `Topic`, `Planner`, `Storage` (OOP); plan kept as dict `{date: [(topic, hours)]}`.
  - Add / delete exams and topics (to change one: delete and add again) through forms in the window, with input validation.
  - Plan rule: hours per topic = difficulty (1-5); daily limit default 4 h (editable); topics ordered by
    exam date then difficulty (hard first); last day before an exam is revision; nothing planned after an exam.
  - Replan: undone topics from past days move forward from today; warn if they no longer fit.
  - Mark a topic done / missed.
  - Workload calendar: month grid, cell colour = hours that day (low to over the limit), click a day to
    see its topics.
  - Dropdowns: common subjects and typical topics (planner/catalog.py), custom text still allowed.
  - Auto difficulty: dict of subject/topic word stems -> difficulty (1-5), user can override per topic.
  - Gantt chart tab (tk.Canvas): a bar per topic, revision bars, exam lines, today line, done/at-risk rows.
  - CSV load/save (`exams.csv`, `topics.csv`) in a data folder; broken/missing file handled gracefully.
  - Custom exceptions and try/except around input, dates and file I/O.
- Out: editing in place, accounts, notifications, cloud sync, mobile app, packaging to .exe.

## Acceptance criteria
- [ ] Adding an exam with a past date, empty name, or bad date format shows a Russian error message and does not crash.
- [ ] Topic difficulty outside 1-5 or non-numeric is rejected with a message.
- [ ] For 2 exams and 6 topics, the plan never exceeds the daily limit (unit test) and all topics are scheduled before their exam.
- [ ] Day before each exam contains only revision.
- [ ] If a topic is missed, "Replan" moves it to a later day before the exam; if it cannot fit, the window warns which topic is at risk.
- [ ] Calendar shows each day coloured by load; clicking a day lists its topics and hours.
- [ ] Data survives restart (CSV); deleting or corrupting the CSV leads to an empty planner with a message, not a crash.
- [ ] Core uses dicts, classes and exception handling (visible in code review of the project).
- [ ] `pytest` passes; planner logic has tests for normal, edge and error cases.
- [ ] README (Russian) explains how to run: `python main.py`.

## Risks
- Too many topics for the days left: handled by the "at risk" warning, not by exceeding the limit.
- tkinter look varies by OS: keep to ttk widgets and a small palette.
- pytest is not installed on this Mac: needs the user's OK to install (dependency).
