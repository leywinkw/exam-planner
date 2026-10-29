from planner.models import DONE
from planner.scheduler import REVISION

TODO_BAR, REVISION_BAR, DONE_ROW, RISK_ROW = "todo", "revision", "done", "risk"


def gantt_rows(planner, at_risk=()):
    # строки для диаграммы Ганта, у каждой есть exam, name, start, end и kind
    # у тем в плане есть полоска, у выполненных и не успеваемых только строка без дат
    span = {}  # (событие, тема) и [первый день, последний день]
    for day, items in planner.plan.items():
        for exam, topic, _ in items:
            first_last = span.setdefault((exam, topic), [day, day])
            first_last[0] = min(first_last[0], day)
            first_last[1] = max(first_last[1], day)

    risk_keys = {t.key for t in at_risk}
    rows = []
    for (exam, topic), (start, end) in span.items():
        kind = REVISION_BAR if topic == REVISION else TODO_BAR
        rows.append({"exam": exam, "name": topic, "start": start, "end": end, "kind": kind})
    for topic in planner.topics.values():
        if topic.key in risk_keys:
            rows.append({"exam": topic.exam, "name": topic.name, "start": None, "end": None, "kind": RISK_ROW})
        elif topic.status == DONE:
            rows.append({"exam": topic.exam, "name": topic.name, "start": None, "end": None, "kind": DONE_ROW})

    def sort_key(row):
        exam_date = planner.exams[row["exam"]].date
        has_bar = row["start"] is not None
        return (exam_date, row["exam"], not has_bar, row["start"] or exam_date, row["name"])

    rows.sort(key=sort_key)
    return rows
