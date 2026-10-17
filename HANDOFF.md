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

## Auto difficulty (2026-10-17)
- planner/estimator.py (dict of stems), Planner.add_topic/set_difficulty accept "авто"; UI: combobox "авто/1-5" + button to change selected topic. 55 tests green. Dictionary is a first guess: user may want to extend it for their real subjects.

## Next
1. Gantt tab done (ui/gantt.py on Canvas, planner/ganttview.py + tests, 45 green); look not seen by me, user to check the tab.
2. Close; optional polish.
