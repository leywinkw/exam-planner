import csv
import os
from datetime import date
from pathlib import Path

from planner.errors import PlannerError, StorageError, ValidationError
from planner.models import EXAM, Topic, parse_date
from planner.scheduler import Planner

EXAMS_FILE, TOPICS_FILE, SETTINGS_FILE = "exams.csv", "topics.csv", "settings.csv"


class Storage:
    # хранит план в трёх csv файлах, exams.csv, topics.csv и settings.csv

    def __init__(self, folder="data"):
        self.folder = Path(folder)

    def save(self, planner):
        # записывает события, темы и настройки, если не вышло, будет StorageError
        try:
            self.folder.mkdir(parents=True, exist_ok=True)
            self._write(EXAMS_FILE, ["name", "date", "kind"],
                        [[e.name, e.date.isoformat(), e.kind] for e in planner.exams.values()])
            self._write(TOPICS_FILE, ["exam", "name", "difficulty", "status", "planned_day"],
                        [[t.exam, t.name, t.difficulty, t.status,
                          t.planned_day.isoformat() if t.planned_day else ""]
                         for t in planner.topics.values()])
            self._write(SETTINGS_FILE, ["key", "value"], [["daily_limit", planner.daily_limit], ["max_chunk", planner.max_chunk]])
        except OSError as error:
            raise StorageError(f"Не удалось сохранить данные: {error.strerror}") from error

    def load(self, today=None):
        # читает файлы и возвращает (planner, warnings), если файлы битые, начинаем с пустого плана
        planner = Planner()
        warnings = []
        try:
            # читаем события, date.min нужен чтобы старые даты из файла не считались ошибкой
            for row in self._read(EXAMS_FILE):
                planner.add_exam(row["name"], parse_date(row["date"]), today=date.min,
                                 kind=row.get("kind") or EXAM)
            for row in self._read(TOPICS_FILE):
                planned = parse_date(row["planned_day"]) if row.get("planned_day") else None
                topic = Topic(row["exam"], row["name"], row["difficulty"], row["status"], planned)
                if topic.exam not in planner.exams or topic.key in planner.topics:
                    raise ValidationError("тема без экзамена или повторяется")
                planner.topics[topic.key] = topic
            for row in self._read(SETTINGS_FILE):
                if row["key"] == "daily_limit":
                    planner.set_daily_limit(row["value"])
                elif row["key"] == "max_chunk":
                    planner.set_max_chunk(row["value"])
        # если что-то не так с файлами, делаем копии .bak и начинаем с пустого плана
        except (PlannerError, KeyError, csv.Error, UnicodeDecodeError, OSError) as error:
            self._backup_broken()
            warnings.append(f"Файлы данных повреждены ({error}). Копии сохранены как *.bak, "
                            "начинаем с пустого плана")
            return Planner(), warnings
        planner.build_plan(today)  # сразу строим план
        return planner, warnings

    def _backup_broken(self):
        # переименовывает битые файлы в .bak, чтобы не потерять данные
        for filename in (EXAMS_FILE, TOPICS_FILE, SETTINGS_FILE):
            path = self.folder / filename
            if path.exists():
                try:
                    os.replace(path, path.with_suffix(".csv.bak"))
                except OSError:
                    pass

    def _write(self, filename, header, rows):
        path = self.folder / filename
        temp = path.with_suffix(".tmp")  # сначала пишем во временный файл

        with open(temp, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(header)
            writer.writerows(rows)
        os.replace(temp, path)  # подменяем файл целиком, так при сбое не останется половина файла

    def _read(self, filename):
        path = self.folder / filename
        if not path.exists():
            return []
        with open(path, newline="", encoding="utf-8-sig") as file:  # utf-8-sig нужен, потому что Excel добавляет в начало файла служебный символ
            return list(csv.DictReader(file))

