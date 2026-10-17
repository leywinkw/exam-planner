# Handoff — exam-planner

## Status
- 2026-10-16 · slices 1-2 built, reviewed, committed · stage: ready for final close

## Decisions
- tkinter workload calendar, CSV storage, forms in the window, standard library only.
- No dev.py project kind fits: project created by hand, git initialised, no dev.py check yet.

## Done
- planner/: errors, models (Exam, Topic, validation), scheduler (Planner: plan dict, build_plan, replan), storage (CSV, corrupt files -> empty planner + warning).
- tests/: 34 pytest tests green (`.venv/bin/pytest`). pytest lives in project .venv (gitignored).

- ui/app.py + main.py: tkinter window (exam/topic forms, status buttons, daily limit, replan, month calendar coloured by load, day details). README.md in Russian. 37 tests green. Window logic smoke-tested with mocked dialogs.

## Not verified
- Look of the window was NOT seen (screenshot permission denied): user should run `python3 main.py` and report visual issues.

## Review (2026-10-17)
- reviewer found 1 HIGH (study placed on another exam's revision day) + MED/LOW: all fixed except formula-injection in CSV (low, accepted) and in-place editing (removed from scope: delete + add). Replan now uses topics.csv `planned_day`. Broken CSV is moved to *.bak; saves are atomic.
- 43 tests green. User saw the window: looks fine.

## Next
1. Close: client-style handover not needed (course project). Optional: Gantt chart or more tkinter polish.
