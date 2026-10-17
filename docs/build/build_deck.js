// Builds the defence presentation. Run from docs/build:
//   NODE_PATH=<folder with node_modules of pptxgenjs> node build_deck.js
// Screenshots are read from ../screens/*.png; a grey placeholder is drawn where one is missing.
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const SCREENS = path.join(__dirname, "..", "screens");
const OUT = path.join(__dirname, "..", "Презентация_Планировщик_экзаменов.pptx");

const INK = "1E1B4B", ACCENT = "4F46E5", SOFT = "E0E7FF", PAGE = "F4F6FB", TEXT = "0F172A";
const MUTED = "64748B", WHITE = "FFFFFF", EXAM = "F87171", CONTROL = "A78BFA", GREEN = "34D399";
const HEAD = "Cambria", BODY = "Calibri", MONO = "Courier New";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5 in
pres.title = "Планировщик подготовки к экзаменам";
pres.author = "Проект №60";
pres.theme = { headFontFace: HEAD, bodyFontFace: BODY };

pres.defineSlideMaster({
  title: "TITLE",
  background: { color: INK },
  objects: [],
  slideNumber: undefined,
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: PAGE },
  objects: [
    { text: { text: "Планировщик подготовки к экзаменам", options: { x: 0.6, y: 7.0, w: 6, h: 0.3, fontFace: BODY, fontSize: 10, color: MUTED, margin: 0 } } },
  ],
  slideNumber: { x: 12.0, y: 7.0, w: 0.8, h: 0.3, fontFace: BODY, fontSize: 10, color: MUTED, align: "right" },
});

// ---- helpers ---------------------------------------------------------
function pngSize(file) {
  const buf = fs.readFileSync(file);
  return { w: buf.readUInt32BE(16), h: buf.readUInt32BE(20) };
}

function title(slide, text) {
  slide.addText(text, { x: 0.6, y: 0.35, w: 12.1, h: 0.9, fontFace: HEAD, fontSize: 34, bold: true,
    color: INK, margin: 0, valign: "middle", isTextBox: true, objectName: "Title" });
}

function card(slide, x, y, w, h, fill) {
  slide.addShape(pres.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.12, fill: { color: fill || WHITE },
    line: { color: "DBE3EE", width: 0.75 }, shadow: { type: "outer", color: "000000", opacity: 0.08, blur: 6, offset: 2, angle: 90 } });
}

function circle(slide, x, y, d, label, fill) {
  slide.addShape(pres.ShapeType.ellipse, { x, y, w: d, h: d, fill: { color: fill || ACCENT }, line: { color: fill || ACCENT } });
  slide.addText(label, { x, y, w: d, h: d, align: "center", valign: "middle", fontFace: BODY, fontSize: 16,
    bold: true, color: WHITE, margin: 0, isTextBox: true });
}

// Screenshot fitted into the box (keeps aspect ratio); grey placeholder when the file does not exist yet.
function shot(slide, name, x, y, w, h) {
  const file = path.join(SCREENS, name);
  if (fs.existsSync(file)) {
    const s = pngSize(file);
    const k = Math.min(w / s.w, h / s.h);
    const iw = s.w * k, ih = s.h * k;
    slide.addShape(pres.ShapeType.rect, { x: x + (w - iw) / 2 - 0.03, y: y + (h - ih) / 2 - 0.03, w: iw + 0.06, h: ih + 0.06,
      fill: { color: WHITE }, line: { color: "CBD5E1", width: 0.75 } });
    slide.addImage({ path: file, x: x + (w - iw) / 2, y: y + (h - ih) / 2, w: iw, h: ih,
      altText: "Скриншот программы: " + name });
  } else {
    slide.addShape(pres.ShapeType.rect, { x, y, w, h, fill: { color: "E2E8F0" }, line: { color: "94A3B8", width: 1, dashType: "dash" } });
    slide.addText("Здесь будет скриншот\n" + name, { x, y, w, h, align: "center", valign: "middle", fontFace: BODY,
      fontSize: 16, color: MUTED, isTextBox: true });
  }
}

function bullets(slide, items, opts) {
  const runs = items.map((t, i) => ({ text: t, options: { bullet: { indent: 18 }, breakLine: i < items.length - 1, paraSpaceAfter: 8 } }));
  slide.addText(runs, Object.assign({ fontFace: BODY, fontSize: 18, color: TEXT, valign: "top", margin: 0, isTextBox: true }, opts));
}

function content(titleText, notes) {
  const s = pres.addSlide({ masterName: "CONTENT" });
  title(s, titleText);
  s.addNotes(notes);
  return s;
}

// ---- 1. title ----------------------------------------------------------
{
  const s = pres.addSlide({ masterName: "TITLE" });
  s.addText("Планировщик подготовки\nк экзаменам", { x: 0.8, y: 1.7, w: 11.7, h: 2.2, fontFace: HEAD, fontSize: 54,
    bold: true, color: WHITE, margin: 0, valign: "top", isTextBox: true });
  s.addText("Проект №60 · итоговый проект по Python", { x: 0.8, y: 4.2, w: 11.7, h: 0.6, fontFace: BODY, fontSize: 24,
    color: "C7D2FE", margin: 0, isTextBox: true });
  s.addText("Автор: [ФИО], группа [номер]", { x: 0.8, y: 6.2, w: 11.7, h: 0.5, fontFace: BODY, fontSize: 18,
    color: "A5B4FC", margin: 0, isTextBox: true });
  // little calendar motif: coloured day cells
  const cols = [SOFT, "BBF7D0", "FDE68A", "FDBA74", EXAM, CONTROL];
  cols.forEach((c, i) => s.addShape(pres.ShapeType.roundRect, { x: 0.8 + i * 0.62, y: 5.2, w: 0.5, h: 0.5, rectRadius: 0.08,
    fill: { color: c }, line: { color: c } }));
  s.addNotes("Здравствуйте! Меня зовут [ФИО]. Мой проект номер 60 — планировщик подготовки к экзаменам. " +
    "Это программа на Python, которая сама раскладывает темы по дням и пересчитывает план, если вы отстаёте.");
}

// ---- 2. task -----------------------------------------------------------
{
  const s = content("Задача",
    "Задача из задания: пользователь вводит экзамены, даты и темы с оценкой сложности, программа распределяет, " +
    "что учить каждый день, и пересчитывает план, если человек отстаёт. Результат нужно показать наглядно — " +
    "я сделал календарь нагрузки и диаграмму Ганта. Минимальные требования курса — обработка ошибок, словари и ООП — выполнены, " +
    "визуализация добавлена как четвёртый критерий.");
  s.addText("Студент вводит экзамены, даты и темы со сложностью. Программа сама решает, что учить каждый день, и пересчитывает план, если студент отстаёт.",
    { x: 0.6, y: 1.5, w: 12.1, h: 1.0, fontFace: BODY, fontSize: 20, color: TEXT, margin: 0, valign: "top", isTextBox: true });
  const steps = [["1", "Ввод", "Экзамены и контрольные с датами, темы со сложностью"],
    ["2", "Распределение", "Темы по дням с лимитом часов, сложные раньше"],
    ["3", "Пересчёт", "Если отстал — невыполненное переезжает вперёд, программа предупреждает о риске"]];
  steps.forEach((st, i) => {
    const x = 0.6 + i * 4.1;
    card(s, x, 2.8, 3.9, 2.3);
    circle(s, x + 0.25, 3.05, 0.6, st[0]);
    s.addText(st[1], { x: x + 1.0, y: 3.05, w: 2.7, h: 0.6, fontFace: HEAD, fontSize: 22, bold: true, color: INK, margin: 0, valign: "middle", isTextBox: true });
    s.addText(st[2], { x: x + 0.25, y: 3.85, w: 3.4, h: 1.1, fontFace: BODY, fontSize: 16, color: TEXT, margin: 0, valign: "top", isTextBox: true });
  });
  s.addText("Требования курса", { x: 0.6, y: 5.4, w: 4, h: 0.4, fontFace: BODY, fontSize: 14, bold: true, color: MUTED, margin: 0, isTextBox: true });
  ["Обработка ошибок", "Словари", "ООП", "Визуализация"].forEach((t, i) => {
    const x = 0.6 + i * 3.1;
    s.addShape(pres.ShapeType.roundRect, { x, y: 5.9, w: 2.9, h: 0.65, rectRadius: 0.3, fill: { color: SOFT }, line: { color: SOFT } });
    s.addText("✓  " + t, { x, y: 5.9, w: 2.9, h: 0.65, align: "center", valign: "middle", fontFace: BODY, fontSize: 18, bold: true,
      color: ACCENT, margin: 0, isTextBox: true });
  });
}

// ---- 3. tools ----------------------------------------------------------
{
  const s = content("Использованные инструменты",
    "Проект написан только на стандартной библиотеке Python, ничего дополнительно устанавливать для запуска не нужно. " +
    "Окно и формы сделаны на tkinter, диаграмма Ганта нарисована на его Canvas. Данные хранятся в CSV-файлах. " +
    "Для проверки логики использован pytest, для истории изменений — git.");
  const tools = [["Python 3", "язык программирования"], ["tkinter + ttk", "окно, формы, списки, вкладки"],
    ["tkinter Canvas", "диаграмма Ганта"], ["csv, pathlib", "хранение данных в файлах"],
    ["datetime, calendar", "даты и календарь месяца"], ["pytest", "70 автотестов"],
    ["git", "история версий проекта"], ["Без сторонних пакетов", "только стандартная библиотека"]];
  tools.forEach((t, i) => {
    const col = i % 4, row = Math.floor(i / 4);
    const x = 0.6 + col * 3.07, y = 1.7 + row * 2.45;
    const hl = i === 7;
    card(s, x, y, 2.87, 2.15, hl ? ACCENT : WHITE);
    s.addText(t[0], { x: x + 0.2, y: y + 0.3, w: 2.47, h: 0.9, fontFace: HEAD, fontSize: 22, bold: true, color: hl ? WHITE : INK, margin: 0, valign: "top", isTextBox: true });
    s.addText(t[1], { x: x + 0.2, y: y + 1.3, w: 2.47, h: 0.7, fontFace: BODY, fontSize: 16, color: hl ? "E0E7FF" : MUTED, margin: 0, valign: "top", isTextBox: true });
  });
}

// ---- 4. structure ------------------------------------------------------
{
  const s = content("Структура проекта",
    "Проект разделён на три части. Папка planner — вся логика: классы экзамена и темы, планировщик, оценка сложности, чтение и запись файлов. " +
    "Папка ui — окно tkinter. Данные лежат в трёх CSV-файлах. Логика ничего не знает про окно, поэтому её можно проверять тестами без запуска интерфейса.");
  const box = (x, w, head, files, fill) => {
    card(s, x, 1.6, w, 4.3, fill);
    s.addText(head, { x: x + 0.25, y: 1.8, w: w - 0.5, h: 0.5, fontFace: HEAD, fontSize: 22, bold: true, color: INK, margin: 0, isTextBox: true });
    s.addText(files.map((f, i) => ({ text: f, options: { breakLine: i < files.length - 1, paraSpaceAfter: 4 } })),
      { x: x + 0.25, y: 2.45, w: w - 0.5, h: 3.3, fontFace: MONO, fontSize: 14, color: TEXT, margin: 0, valign: "top", isTextBox: true });
  };
  box(0.6, 4.0, "ui/ — окно", ["app.py      главное окно", "gantt.py    диаграмма Ганта", "dialogs.py  «Несколько тем»", "widgets.py  подсказки", "theme.py    цвета и стили"]);
  box(5.15, 4.3, "planner/ — логика", ["models.py     Exam, Topic", "scheduler.py  Planner", "estimator.py  сложность", "catalog.py    предметы, темы", "storage.py    CSV", "errors.py     свои ошибки"], WHITE);
  box(10.0, 2.73, "data/ — CSV", ["exams.csv", "topics.csv", "settings.csv"]);
  s.addText("→", { x: 4.6, y: 3.3, w: 0.55, h: 0.8, align: "center", valign: "middle", fontFace: BODY, fontSize: 36, color: ACCENT, margin: 0, isTextBox: true });
  s.addText("→", { x: 9.45, y: 3.3, w: 0.55, h: 0.8, align: "center", valign: "middle", fontFace: BODY, fontSize: 36, color: ACCENT, margin: 0, isTextBox: true });
  s.addText("Логика не зависит от окна — её проверяют тесты без интерфейса", { x: 0.6, y: 6.2, w: 12.1, h: 0.5, fontFace: BODY, fontSize: 18,
    italic: true, color: ACCENT, margin: 0, isTextBox: true });
}

// ---- 5. features -------------------------------------------------------
{
  const s = content("Реализованный функционал",
    "Что умеет программа. Можно добавлять экзамены и контрольные работы с датами. Темы выбираются из выпадающих списков или вводятся вручную, " +
    "можно добавить сразу несколько. Сложность подбирается автоматически по названию, её можно поправить. План учитывает лимит часов в день " +
    "и не ставит большую тему на один день. Если отстал — кнопка «Перепланировать». Всё показывается в календаре и на диаграмме Ганта и сохраняется в файлы.");
  const items = [["Экзамены и контрольные", "у каждого своя дата и свои темы"],
    ["Выпадающие списки", "типовые предметы и темы, можно вписать своё, добавить сразу несколько тем"],
    ["Автоподбор сложности", "по названию предмета и темы, можно поправить вручную"],
    ["План по дням", "лимит часов в день и на тему, сложные темы раньше"],
    ["Перепланирование", "отстал — темы переезжают вперёд, предупреждение о риске"],
    ["Два вида визуализации", "календарь нагрузки и диаграмма Ганта"],
    ["Сохранение в CSV", "данные не пропадают, повреждённый файл не ломает программу"]];
  items.forEach((it, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = 0.6 + col * 6.15, y = 1.55 + row * 1.35;
    card(s, x, y, 5.95, 1.2);
    circle(s, x + 0.2, y + 0.3, 0.6, String(i + 1));
    s.addText(it[0], { x: x + 1.0, y: y + 0.12, w: 4.8, h: 0.42, fontFace: HEAD, fontSize: 18, bold: true, color: INK, margin: 0, isTextBox: true });
    s.addText(it[1], { x: x + 1.0, y: y + 0.55, w: 4.8, h: 0.6, fontFace: BODY, fontSize: 14, color: MUTED, margin: 0, valign: "top", isTextBox: true });
  });
}

// ---- 6. algorithm ------------------------------------------------------
{
  const s = content("Как строится план",
    "Правила распределения. Сложность от одного до пяти равна числу часов на тему. В день не больше четырёх часов и не больше двух часов одной темы, " +
    "поэтому большая тема растягивается на несколько дней — на схеме тема на пять часов превращается в два, два и один час. " +
    "Сначала идут самые сложные темы ближайшего экзамена. Накануне экзамена — только повторение, в сам день ничего не планируется.");
  s.addText([
    { text: "Часов на тему = сложность (1–5)", options: { bullet: { indent: 18 }, breakLine: true, paraSpaceAfter: 10 } },
    { text: "В день не больше 4 часов, одной темы — не больше 2", options: { bullet: { indent: 18 }, breakLine: true, paraSpaceAfter: 10 } },
    { text: "Сложные темы ближайшего срока — первыми", options: { bullet: { indent: 18 }, breakLine: true, paraSpaceAfter: 10 } },
    { text: "За день до экзамена — повторение 2 ч (до контрольной — 1 ч)", options: { bullet: { indent: 18 }, breakLine: true, paraSpaceAfter: 10 } },
    { text: "Не помещается — предупреждение, а не перегруз", options: { bullet: { indent: 18 } } },
  ], { x: 0.6, y: 1.6, w: 6.0, h: 4.6, fontFace: BODY, fontSize: 18, color: TEXT, valign: "top", margin: 0, isTextBox: true });
  card(s, 7.0, 1.6, 5.73, 4.6);
  s.addText("Тема на 5 часов", { x: 7.3, y: 1.8, w: 5.1, h: 0.45, fontFace: HEAD, fontSize: 20, bold: true, color: INK, margin: 0, isTextBox: true });
  const days = [["Пн", 2], ["Вт", 2], ["Ср", 1], ["Чт", 0], ["Пт", 0]];
  days.forEach((d, i) => {
    const x = 7.3 + i * 1.0;
    const hh = d[1] * 0.9;
    s.addShape(pres.ShapeType.rect, { x, y: 4.9 - hh, w: 0.8, h: hh || 0.02, fill: { color: d[1] ? ACCENT : "CBD5E1" }, line: { color: d[1] ? ACCENT : "CBD5E1" } });
    if (d[1]) s.addText(d[1] + " ч", { x, y: 4.9 - hh, w: 0.8, h: hh, align: "center", valign: "middle", fontFace: BODY, fontSize: 16, bold: true, color: WHITE, margin: 0, isTextBox: true });
    s.addText(d[0], { x, y: 5.0, w: 0.8, h: 0.35, align: "center", fontFace: BODY, fontSize: 14, color: MUTED, margin: 0, isTextBox: true });
  });
  s.addText("2 + 2 + 1 вместо 5 ч в один день", { x: 7.3, y: 5.5, w: 5.1, h: 0.5, fontFace: BODY, fontSize: 16, italic: true, color: ACCENT, margin: 0, isTextBox: true });
}

// ---- 7. course requirements (code) ---------------------------------------
{
  const s = content("Требования курса в коде",
    "Как выполнены обязательные требования. Обработка ошибок: все проверки ввода бросают свои исключения, а окно ловит их через try и except и показывает понятное сообщение, " +
    "программа не падает. Словари: план — это словарь «дата — список занятий», а оценка сложности — словарь основ предметов и слов-поправок. " +
    "ООП: классы Exam, Topic, Planner, Storage, окно и диаграмма тоже классы, а ошибки образуют иерархию.");
  const cols = [["Обработка ошибок", "try:\n    action()\nexcept PlannerError as e:\n    messagebox.showerror(\n        \"Ошибка\", str(e))\n\nValidationError,\nStorageError"],
    ["Словари", "plan = {\n  date(2026, 10, 3): [\n    (\"Математика\",\n     \"Ряды\", 2)]\n}\n\nSUBJECT_BASE = {\n  \"математ\": 4,\n  \"физик\": 4, ...}"],
    ["ООП", "class Planner:\n    def build_plan(self)\n    def replan(self)\n\nclass Exam, Topic\nclass Storage\nclass GanttChart(\n    ttk.Frame)\nclass PlannerError(\n    Exception)"]];
  cols.forEach((c, i) => {
    const x = 0.6 + i * 4.1;
    card(s, x, 1.55, 3.9, 5.2);
    s.addText(c[0], { x: x + 0.25, y: 1.7, w: 3.4, h: 0.5, fontFace: HEAD, fontSize: 22, bold: true, color: ACCENT, margin: 0, isTextBox: true });
    s.addText(c[1], { x: x + 0.25, y: 2.3, w: 3.4, h: 4.3, fontFace: MONO, fontSize: 13, color: TEXT, margin: 0, valign: "top", isTextBox: true });
  });
}

// ---- 8. calendar screenshot ---------------------------------------------
{
  const s = content("Календарь нагрузки",
    "Первый вид визуализации — календарь на месяц. Цвет клетки показывает, сколько часов запланировано: чем темнее, тем ближе к лимиту. " +
    "Экзамены отмечены красным, контрольные — фиолетовым. По клику на день внизу видно, какие темы и сколько часов в этот день.");
  shot(s, "01_calendar.png", 0.6, 1.4, 8.3, 5.4);
  card(s, 9.2, 1.4, 3.53, 5.4);
  bullets(s, ["Цвет — загрузка дня", "Красный — экзамен, фиолетовый — контрольная", "Клик по дню — список тем и часов", "Листание месяцев"],
    { x: 9.45, y: 1.65, w: 3.1, h: 4.9, fontSize: 16 });
}

// ---- 9. gantt screenshot ------------------------------------------------
{
  const s = content("Диаграмма Ганта",
    "Второй вид визуализации — диаграмма Ганта. Каждая тема — полоска от первого до последнего дня занятий, полоски сгруппированы по экзаменам. " +
    "Вертикальные линии — даты экзаменов и контрольных, пунктирная — сегодня. Выполненные темы и темы, которые не помещаются до срока, показаны отдельными строками.");
  shot(s, "02_gantt.png", 0.6, 1.4, 8.3, 5.4);
  card(s, 9.2, 1.4, 3.53, 5.4);
  bullets(s, ["Полоска — период занятий по теме", "Линии — экзамены, контрольные и «сегодня»", "Красная строка — тема не помещается", "Серая — тема уже выполнена"],
    { x: 9.45, y: 1.65, w: 3.1, h: 4.9, fontSize: 16 });
}

// ---- 10. input / output -------------------------------------------------
{
  const s = content("Примеры ввода и вывода",
    "Проверка ввода. Пустое название, неверная дата, дата в прошлом, повтор — для каждого случая программа показывает понятное сообщение и не падает. " +
    "Для названия «Введение в анализ» по математике сложность подбирается автоматически и получается два. " +
    "Справа — скриншоты: окно добавления нескольких тем и сообщение об ошибке.");
  const rows = [["Ввод", "Результат"],
    ["Экзамен «Математика», 11.10.2026", "Добавлен"],
    ["Экзамен с пустым названием", "Укажите название экзамена"],
    ["Дата «32.13.2026»", "Дата должна быть в формате ДД.ММ.ГГГГ"],
    ["Дата 20.09.2026 (прошла)", "Дата должна быть в будущем"],
    ["Сложность 9", "Сложность должна быть от 1 до 5"],
    ["«Введение в анализ», «авто»", "Сложность 2"],
    ["Повреждённый файл данных", "Сообщение и копия .bak, программа работает"]];
  const tbl = rows.map((r, i) => r.map((c) => ({ text: c, options: { bold: i === 0, color: i === 0 ? WHITE : TEXT,
    fill: { color: i === 0 ? INK : (i % 2 ? WHITE : "EEF2FF") }, fontFace: BODY, fontSize: 14, valign: "middle" } })));
  s.addTable(tbl, { x: 0.6, y: 1.5, w: 7.4, colW: [3.3, 4.1], rowH: 0.62, border: { type: "solid", color: "DBE3EE", pt: 0.75 }, margin: [0.05, 0.12, 0.05, 0.12] });
  shot(s, "03_dialog.png", 8.3, 1.5, 4.43, 2.8);
  shot(s, "04_error.png", 8.3, 4.5, 4.43, 2.2);
}

// ---- 11. tests -----------------------------------------------------------
{
  const s = content("Тестирование",
    "Логика проверена семьюдесятью автоматическими тестами на pytest, все проходят. Тесты проверяют неверный ввод, лимиты часов, " +
    "день повторения, распределение по дням, перепланирование, автоподбор сложности и работу с повреждёнными файлами. " +
    "Окно проверялось вручную и скриптами с подменой диалогов.");
  card(s, 0.6, 1.6, 4.2, 4.6, INK);
  s.addText("70", { x: 0.6, y: 2.0, w: 4.2, h: 1.9, align: "center", valign: "middle", fontFace: HEAD, fontSize: 110, bold: true, color: WHITE, margin: 0, isTextBox: true });
  s.addText("автотестов pytest,\nвсе проходят", { x: 0.6, y: 4.0, w: 4.2, h: 1.2, align: "center", valign: "top", fontFace: BODY, fontSize: 22, color: "C7D2FE", margin: 0, isTextBox: true });
  bullets(s, ["Неверные даты, сложность, лимиты, повторы", "Лимит часов в день и на тему не превышается",
    "День перед экзаменом — только повторение", "Перепланирование и предупреждение о риске",
    "Автоподбор сложности и списки предметов", "Повреждённые и неполные CSV-файлы"],
    { x: 5.3, y: 1.7, w: 7.4, h: 4.4, fontSize: 20 });
}

// ---- 12. summary -----------------------------------------------------------
{
  const s = pres.addSlide({ masterName: "TITLE" });
  s.addText("Итоги", { x: 0.8, y: 0.8, w: 11.7, h: 1.0, fontFace: HEAD, fontSize: 44, bold: true, color: WHITE, margin: 0, isTextBox: true });
  s.addText([
    { text: "Готовая программа с окном, двумя видами визуализации и сохранением данных", options: { bullet: { indent: 20 }, breakLine: true, paraSpaceAfter: 12 } },
    { text: "Обязательные требования курса выполнены, добавлены визуализация, CSV и тесты", options: { bullet: { indent: 20 }, breakLine: true, paraSpaceAfter: 12 } },
    { text: "Дальше можно: редактирование записей, уведомления, экспорт в календарь", options: { bullet: { indent: 20 } } },
  ], { x: 0.8, y: 2.2, w: 11.7, h: 3.0, fontFace: BODY, fontSize: 22, color: "E0E7FF", valign: "top", margin: 0, isTextBox: true });
  s.addText("Спасибо за внимание! Вопросы?", { x: 0.8, y: 5.6, w: 11.7, h: 0.9, fontFace: HEAD, fontSize: 36, bold: true, color: WHITE, margin: 0, isTextBox: true });
  s.addNotes("Итог: получилась рабочая программа с окном, календарём и диаграммой Ганта, данные сохраняются в файлы, логика покрыта тестами. " +
    "В дальнейшем можно добавить редактирование записей, уведомления и экспорт в календарь. Спасибо за внимание, готов ответить на вопросы.");
}

pres.writeFile({ fileName: OUT }).then((f) => console.log("written", f));
