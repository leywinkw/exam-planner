// Builds the Word report. Run from docs/build:
//   NODE_PATH=<folder with node_modules of docx> node build_report.js
// Screenshots are read from ../screens/*.png; a framed note is drawn where one is missing.
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell, WidthType,
  ShadingType, BorderStyle, LevelFormat, ImageRun, PageBreak, TableOfContents, Footer, PageNumber,
} = require("docx");

const SCREENS = path.join(__dirname, "..", "screens");
const IO_FILE = path.join(__dirname, "..", "io_examples.txt");
const OUT = path.join(__dirname, "..", "Отчёт_Планировщик_экзаменов.docx");
const FONT = "Times New Roman";
const CONTENT_W = 9355; // A4 width 11906 - left 1701 (3 cm) - right 850 (1.5 cm)

// ---- helpers ---------------------------------------------------------------
const run = (text, o = {}) => new TextRun({ text, font: FONT, size: o.size || 28, ...o });
const body = (text, o = {}) => new Paragraph({
  children: Array.isArray(text) ? text : [run(text)],
  alignment: AlignmentType.JUSTIFIED, spacing: { line: 360, after: 120 }, indent: { firstLine: 709 }, ...o,
});
const h1 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [run(text, { bold: true, size: 32 })],
  spacing: { before: 360, after: 200 }, keepNext: true });
const h2 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [run(text, { bold: true, size: 28 })],
  spacing: { before: 240, after: 120 }, keepNext: true });
const bullet = (text) => new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: Array.isArray(text) ? text : [run(text)],
  alignment: AlignmentType.JUSTIFIED, spacing: { line: 360, after: 60 } });
const code = (lines) => lines.map((l, i) => new Paragraph({
  children: [new TextRun({ text: l || " ", font: "Courier New", size: 22 })],
  spacing: { line: 260, after: i === lines.length - 1 ? 200 : 0 },
  shading: { type: ShadingType.CLEAR, fill: "F3F4F6" }, indent: { left: 200, right: 200 },
}));

const border = { style: BorderStyle.SINGLE, size: 4, color: "999999" };
const borders = { top: border, bottom: border, left: border, right: border };
function table(headers, rows, widths) {
  const cell = (text, w, head) => new TableCell({
    borders, width: { size: w, type: WidthType.DXA },
    shading: head ? { type: ShadingType.CLEAR, fill: "E5E7EB" } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({ children: [run(text, { size: 24, bold: head })] })],
  });
  return new Table({
    width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: widths,
    rows: [new TableRow({ tableHeader: true, children: headers.map((h, i) => cell(h, widths[i], true)) }),
      ...rows.map((r) => new TableRow({ children: r.map((c, i) => cell(c, widths[i], false)) }))],
  });
}
const gap = () => new Paragraph({ children: [], spacing: { after: 120 } });

function pngSize(file) {
  const buf = fs.readFileSync(file);
  return { w: buf.readUInt32BE(16), h: buf.readUInt32BE(20) };
}
let figureNo = 0;
function figure(file, caption, maxW = 560) {
  figureNo += 1;
  const full = path.join(SCREENS, file);
  const out = [];
  if (fs.existsSync(full)) {
    const s = pngSize(full);
    const w = Math.min(maxW, s.w), h = Math.round(s.h * (w / s.w));
    out.push(new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120, after: 60 },
      children: [new ImageRun({ type: "png", data: fs.readFileSync(full), transformation: { width: w, height: h },
        altText: { title: caption, description: caption, name: file } })] }));
  } else {
    out.push(new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120, after: 60 },
      border: { top: border, bottom: border, left: border, right: border },
      shading: { type: ShadingType.CLEAR, fill: "F3F4F6" },
      children: [run(`[Здесь будет скриншот: ${file}]`, { size: 24, italics: true, color: "666666" })] }));
  }
  out.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 },
    children: [run(`Рисунок ${figureNo} — ${caption}`, { size: 24 })] }));
  return out;
}

// ---- I/O examples from the real run ---------------------------------------------
const ioText = fs.existsSync(IO_FILE) ? fs.readFileSync(IO_FILE, "utf8").trimEnd().split("\n") : ["(запустите examples/io_demo.py)"];
const planLines = [];
{
  let on = false;
  for (const l of ioText) {
    if (l.startsWith("== 3.")) { on = true; continue; }
    if (l.startsWith("== 4.")) break;
    if (on && l.trim()) planLines.push(l);
  }
}
const replanLines = [];
{
  let on = false;
  for (const l of ioText) {
    if (l.startsWith("== 4.")) { on = true; continue; }
    if (l.startsWith("== 5.")) break;
    if (on && l.trim()) replanLines.push(l);
  }
}

// ---- document --------------------------------------------------------------------
const center = (text, o = {}) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: o.after || 120 },
  children: [run(text, o)] });

const title = [
  center("ОТЧЁТ", { size: 36, bold: true, after: 200 }),
  center("по итоговому проекту по языку Python", { size: 28, after: 1200 }),
  center("Тема: «Планировщик подготовки к экзаменам»", { size: 32, bold: true, after: 100 }),
  center("(проект № 60)", { size: 28, after: 2000 }),
  new Paragraph({ alignment: AlignmentType.RIGHT, spacing: { after: 80 }, children: [run("Выполнили:")] }),
  new Paragraph({ alignment: AlignmentType.RIGHT, spacing: { after: 80 }, children: [run("Дибривный Павел, группа ИСТ04")] }),
  new Paragraph({ alignment: AlignmentType.RIGHT, spacing: { after: 240 }, children: [run("Салазде Георгий, группа ИСТ03")] }),
  new Paragraph({ alignment: AlignmentType.RIGHT, spacing: { after: 1500 }, children: [run("Проверила: Алибалаева Лейла Ибрагимовна")] }),
  center("2026", { size: 28 }),
  new Paragraph({ children: [new PageBreak()] }),
  center("СОДЕРЖАНИЕ", { size: 32, bold: true, after: 200 }),
  new TableOfContents("Содержание", { hyperlink: true, headingStyleRange: "1-2" }),
  new Paragraph({ children: [new PageBreak()] }),
];

const children = [
  ...title,

  h1("1. Постановка задачи"),
  body("Нужно было сделать программу для подготовки к экзаменам. Пользователь вводит экзамены, даты и темы с оценкой сложности. " +
    "Программа сама решает, что учить в каждый день, а если человек отстаёт, пересчитывает план. " +
    "Результат показывается в виде диаграммы Ганта или календаря нагрузки."),
  body("Требования из задания:"),
  bullet("писать на Python и брать только то, что прошли на курсе;"),
  bullet("обязательно использовать обработку ошибок, словари и ООП;"),
  bullet("четвёртым критерием добавить визуализацию (окно tkinter, график и т. п.);"),
  bullet("хранить данные в базе, а если базы нет, то в CSV-файлах или словарях."),
  body("Сверх задания мы сделали контрольные работы (несколько тем на одну дату), автоподбор сложности по названию темы, " +
    "выпадающие списки с типовыми предметами и темами и автотесты."),

  h1("2. Используемые инструменты"),
  table(["Инструмент", "Для чего нужен"], [
    ["Python 3", "основной язык; проект работает на версии 3.9 и новее"],
    ["tkinter, ttk", "окно программы: формы, выпадающие списки, таблицы, вкладки, диалоги, календарь"],
    ["tkinter.Canvas", "рисование диаграммы Ганта"],
    ["модуль csv, pathlib", "хранение данных в файлах exams.csv, topics.csv, settings.csv"],
    ["datetime, calendar", "даты и сетка календаря на месяц"],
    ["pytest", "автоматические тесты логики (83 теста)"],
    ["git", "история изменений проекта"],
  ], [3000, 6355]),
  gap(),
  body("pytest ставится отдельно и нужен только для запуска тестов, сама программа работает без него."),

  h1("3. Структура проекта"),
  body("Код мы разделили на две части: логика лежит в папке planner, окно в папке ui. Логика ничего не знает про окно, " +
    "поэтому тесты проверяют её без запуска интерфейса."),
  ...code([
    "exam-planner/",
    "  main.py            запуск программы",
    "  demo.py            окно с примерными данными (для скриншотов)",
    "  planner/           логика",
    "    models.py        классы Exam, Topic, проверка ввода",
    "    scheduler.py     класс Planner: построение и пересчёт плана",
    "    estimator.py     автоподбор сложности темы (словари)",
    "    catalog.py       типовые предметы и темы для списков",
    "    storage.py       класс Storage: чтение и запись CSV",
    "    calview.py       сетка календаря и цвета нагрузки",
    "    ganttview.py     подготовка строк диаграммы Ганта",
    "    errors.py        собственные исключения",
    "  ui/                окно tkinter",
    "    app.py           главное окно (класс App)",
    "    gantt.py         диаграмма Ганта (класс GanttChart)",
    "    dialogs.py       диалог «Несколько тем»",
    "    widgets.py       поля ввода с подсказкой внутри",
    "    theme.py         цвета и стили",
    "  tests/             автоматические тесты (pytest)",
    "  examples/          примеры ввода-вывода в консоли",
    "  data/              файлы данных CSV",
  ]),

  h1("4. Описание функционала"),
  h2("4.1. Экзамены и контрольные работы"),
  body("Предмет выбирается из выпадающего списка или вводится вручную. Дальше указываются дата в формате ДД.ММ.ГГГГ и тип: " +
    "«Экзамен» или «Контрольная». У каждого события своя дата и свои темы. В списке видно, сколько дней осталось. " +
    "Дата должна быть в будущем, название не может быть пустым, два одинаковых события добавить нельзя."),
  body("Дату можно ввести по-разному. Полная дата записывается как ДД.ММ.ГГГГ. Если написать только число («25»), " +
    "программа возьмёт ближайшее такое число в будущем, а если число и месяц («25.11») — ближайший такой день. " +
    "Результат сразу показывается в поле полной датой. Можно и вовсе не печатать: щелчок по полю открывает " +
    "маленький календарь, где достаточно нажать на нужное число, и оно подставится само. Прошедшие дни в нём недоступны."),
  h2("4.2. Темы и автоподбор сложности"),
  body("После выбора события в списке тем появляются типовые темы по этому предмету (те, что уже добавлены, из списка пропадают). " +
    "Тему можно вписать самому. Кнопка «Несколько…» открывает окно, где отмечаются сразу много тем и дописываются свои через запятую."),
  body("Сложность темы — число от 1 до 5, и она же задаёт число часов. По умолчанию стоит «авто»: программа оценивает сложность " +
    "по названию предмета и темы с помощью словарей. Например, у математики базовая сложность 4, у физкультуры 1, " +
    "слово «введение» её снижает, а «теорема» или «интеграл» повышают. Значение можно задать вручную или поменять у готовой темы."),
  ...figure("03_dialog.png", "Окно добавления нескольких тем", 380),
  h2("4.3. Распределение по дням"),
  body("План пересобирается после каждого изменения. Правила такие:"),
  bullet("часов на тему столько же, какова её сложность;"),
  bullet("часы события делятся поровну на все дни до повторения: если тем мало, занятия идут через день-два, " +
    "а не в первый же день, и срок не остаётся пустым;"),
  bullet("в день ставится не больше заданного числа часов (по умолчанию 4) и не больше 2 часов одной темы, " +
    "поэтому большая тема растягивается на несколько дней по 1–2 часа;"),
  bullet("первыми идут самые сложные темы ближайшего события;"),
  bullet("день перед экзаменом отдан под повторение (2 часа), перед контрольной ставится 1 час, в день самого события занятий нет;"),
  bullet("если темы не помещаются в срок, дни не перегружаются: программа показывает, какие темы под угрозой."),
  h2("4.4. Пересчёт плана"),
  body("Если вы отстали, нажмите «Перепланировать». Для каждой темы мы запоминаем день, на который её поставили. " +
    "Невыполненные темы с прошедшим днём планируются заново с сегодняшнего дня. Программа пишет, что перенесла, " +
    "и предупреждает о темах, которые уже не успеть. Выполненные темы отмечаются кнопкой «Готово» и в плане больше не участвуют."),
  ...figure("s4_risk_gantt.png", "Предупреждение: темы не помещаются до экзамена (лимит 2 часа в день)", 560),
  h2("4.5. Визуализация"),
  body("Календарь показывает месяц. Цвет клетки зависит от загрузки: от серого (свободно) до оранжевого (дошли до лимита часов). " +
    "Экзамены красные, контрольные фиолетовые. Если нажать на день, внизу появится список тем и часов на этот день."),
  ...figure("01_calendar.png", "Календарь нагрузки", 560),
  body("Диаграмму Ганта мы нарисовали на tkinter Canvas. Каждая тема — полоска от первого до последнего дня занятий, " +
    "полоски сгруппированы по событиям. Вертикальные линии отмечают даты экзаменов и контрольных, пунктирная — сегодняшний день. " +
    "Выполненные темы и темы, которые не успеть, показаны отдельными строками."),
  ...figure("02_gantt.png", "Диаграмма Ганта", 560),
  h2("4.6. Хранение данных"),
  body("Данные сохраняются после каждого изменения в три CSV-файла в папке data: exams.csv (события), topics.csv (темы) и " +
    "settings.csv (лимиты часов). Файл сначала пишется во временный, а потом подменяет старый, поэтому сбой посреди записи " +
    "не оставит половину файла. Если файл повреждён, программа не падает: она переименовывает его в .bak, сообщает об этом " +
    "и начинает с пустого плана."),

  h1("5. Описание методов и алгоритмов"),
  h2("5.1. Классы и их методы"),
  table(["Класс / функция", "Что делает"], [
    ["Exam (models.py)", "экзамен или контрольная: название, дата, тип; проверяет данные при создании"],
    ["Topic (models.py)", "тема: событие, название, сложность 1–5, статус, день планирования; свойство hours даёт часы"],
    ["parse_date, parse_difficulty, clean_name", "проверяют и преобразуют введённые значения; при ошибке выбрасывают ValidationError"],
    ["Planner.add_exam, add_topic", "добавляют событие и тему с проверками (дата в будущем, повторы, существует ли событие)"],
    ["Planner.remove_exam, remove_topic", "удаляют событие вместе с темами или одну тему"],
    ["Planner.set_difficulty, set_status", "меняют сложность темы (в том числе на «авто») и статус «готово»"],
    ["Planner.set_daily_limit, set_max_chunk", "задают лимит часов в день и часов одной темы в день, проверяя диапазон"],
    ["Planner.build_plan", "строит словарь плана {дата: [(событие, тема, часы)]} и возвращает темы, не поместившиеся в срок"],
    ["Planner.replan", "находит пропущенные темы, строит план заново и возвращает (перенесённые, под угрозой)"],
    ["Planner.day_load", "считает сумму часов за день для цвета в календаре"],
    ["estimate_difficulty (estimator.py)", "оценивает сложность по названию предмета и темы с помощью словарей"],
    ["subjects, topics_for (catalog.py)", "отдают списки предметов и типовых тем для выпадающих списков"],
    ["Storage.save, Storage.load", "пишут и читают CSV; если файлы повреждены, делают копию .bak и начинают с пустого плана"],
    ["gantt_rows (ganttview.py)", "готовит строки диаграммы: период каждой темы, выполненные и не поместившиеся темы"],
    ["month_weeks, shift_month, load_color", "дают сетку месяца, переход между месяцами и цвет клетки по нагрузке"],
    ["App, GanttChart, MultiTopicDialog (ui)", "главное окно, диаграмма Ганта на Canvas и диалог выбора нескольких тем"],
    ["PlannerError, ValidationError, StorageError", "наши исключения: ошибки ввода и ошибки работы с файлами"],
  ], [3600, 5755]),
  gap(),
  h2("5.2. Алгоритм построения плана"),
  body("Метод build_plan работает так. Сначала собираются закрытые для учёбы дни: дни событий и дни перед ними. " +
    "На день перед каждым событием ставится повторение. Потом события обходятся по возрастанию даты. " +
    "Для каждого события выбираются учебные дни от сегодняшнего до дня за два дня до события, в которых есть свободное время. " +
    "Все часы события (сумма часов его тем) равномерно раскладываются на эти дни: k-й час попадает в день с номером " +
    "floor((k + 0.5) · число дней / число часов). Так занятия растягиваются на весь срок, а не копятся в первых днях. " +
    "Темы идут по убыванию сложности, часы каждого дня отдаются им по очереди, но не больше лимита на тему в день. " +
    "Если из-за лимитов часть часов не встала, она ставится в самые свободные дни срока. " +
    "Что не поместилось даже так, попадает в список «под угрозой»."),
  ...code([
    "закрытые_дни = даты событий и дни перед ними",
    "для каждого события: поставить повторение на день перед ним",
    "для события в порядке возрастания даты:",
    "    дни = учебные дни до (дата события - 2 дня) со свободным временем",
    "    часы = сумма часов тем события",
    "    k-й час -> день номер floor((k + 0.5) * len(дни) / часы)   # равномерно",
    "    для каждого дня: отдать часы дня темам по очереди (сложные первыми),",
    "                     не больше лимита на тему и лимита дня",
    "    остаток -> в самые свободные дни; что не влезло -> «под угрозой»",
  ]),
  body("План лежит в словаре: ключ — дата, значение — список кортежей (событие, тема, часы). " +
    "Такая структура удобна и календарю (сумма часов по ключу), и диаграмме (первый и последний день темы)."),
  h2("5.3. Автоподбор сложности"),
  body("Функция estimate_difficulty использует два словаря. В первом лежит базовая сложность предмета по основе слова " +
    "(«математ» — 4, «литератур» — 2, «физкультур» — 1), для незнакомого предмета берётся 3. Во втором — поправки по словам " +
    "в названии темы («введени» даёт минус 2, «основ» минус 1, «теорем» плюс 1). Итог ограничивается числами от 1 до 5."),
  h2("5.4. Обработка ошибок"),
  body("Проверки ввода выбрасывают наши собственные исключения: ValidationError (неверная дата, пустое название, " +
    "сложность вне диапазона, повтор) и StorageError (не удалось записать файл). Оба наследуются от PlannerError. " +
    "В окне действия выполняются внутри try, а ошибка показывается сообщением в диалоге, так что программа не вылетает."),
  ...code([
    "def _run(self, action):",
    "    try:",
    "        action()",
    "    except PlannerError as error:",
    "        messagebox.showerror(\"Ошибка\", str(error))",
    "        return False",
    "    return True",
  ]),

  h1("6. Соответствие требованиям задания"),
  table(["Требование", "Что сделано"], [
    ["Обработка ошибок", "собственные исключения, try/except в окне и при работе с файлами, битые файлы не ломают программу"],
    ["Словари", "план {дата: [занятия]}, словари основ предметов и поправок сложности, каталог предметов и тем, события и темы в словарях класса Planner"],
    ["ООП", "классы Exam, Topic, Planner, Storage, App, GanttChart, MultiTopicDialog и иерархия исключений"],
    ["Визуализация", "календарь нагрузки и диаграмма Ганта в окне tkinter"],
    ["Хранение данных", "файлы CSV (базу данных не использовали)"],
    ["Сверх задания", "автотесты pytest, автоподбор сложности, контрольные работы, выпадающие списки"],
  ], [2800, 6555]),

  h1("7. Тестирование"),
  h2("7.1. Автоматические тесты"),
  body("Логику проверяют 83 автотеста на pytest (папка tests). Они смотрят, как программа реагирует на неверные даты, " +
    "сложность и лимиты, не превышаются ли лимиты часов, остаётся ли день перед экзаменом только под повторение, " +
    "как тема растягивается по дням, как работают перепланирование, автоподбор сложности и списки предметов. " +
    "Отдельно проверено чтение и запись CSV: повреждённые и неполные файлы, файлы с BOM. Результат запуска: 83 passed."),
  h2("7.2. Примеры ввода и вывода"),
  body("Ниже реальный вывод программы: скрипт examples/io_demo.py с фиксированной датой «сегодня» 01.10.2026."),
  table(["Ввод", "Результат"], [
    ["Экзамен «Математика», 11.10.2026", "добавлен"],
    ["Экзамен с пустым названием", "Укажите название экзамена"],
    ["Дата «32.13.2026»", "Дата должна быть в формате ДД.ММ.ГГГГ"],
    ["Дата 20.09.2026 (уже прошла)", "Дата должна быть в будущем"],
    ["Повторное добавление «Математика»", "Такое событие уже есть"],
    ["Тема «Введение в анализ», сложность «авто»", "сложность 2"],
    ["Тема «Интегралы», сложность «авто»", "сложность 5"],
    ["Сложность 9", "Сложность должна быть от 1 до 5"],
    ["Сложность «abc»", "Сложность должна быть целым числом от 1 до 5"],
    ["Лимит часов в день = 0", "Лимит часов в день: от 1 до 16"],
  ], [4300, 5055]),
  gap(),
  body("Построенный план для двух событий: экзамен по математике 11.10 и контрольная по физике 06.10 " +
    "(лимит 4 часа в день, не больше 2 часов одной темы):"),
  ...code(planLines),
  body("Перепланирование через 3 дня, когда пользователь отстал:"),
  ...code(replanLines),
  ...figure("04_error.png", "Сообщение об ошибке при вводе неверной даты", 420),

  h1("8. Запуск программы"),
  body("Код проекта лежит в репозитории на GitHub: https://github.com/leywinkw/exam-planner (публичный репозиторий)."),
  ...code(["cd exam-planner", "python3 main.py"]),
  body("Нужен Python 3.9 или новее с tkinter (он есть в стандартной установке). Для тестов создайте виртуальное окружение, " +
    "поставьте pytest и запустите pytest. Окно с примерными данными открывает python3 demo.py, а скрипт screenshots.py " +
    "сам проводит программу по сценарию и сохраняет скриншоты для отчёта и презентации (только macOS)."),

  h1("9. Заключение"),
  body("Мы сделали планировщик подготовки к экзаменам. Он принимает экзамены и контрольные с темами, сам подбирает сложность, " +
    "раскладывает темы по дням с учётом лимитов, пересчитывает план, когда человек отстаёт, и показывает результат в календаре " +
    "и на диаграмме Ганта. Требования курса (ошибки, словари, ООП) и четвёртый критерий (визуализация) выполнены, " +
    "данные лежат в CSV, а логику проверяют тесты. Что можно добавить дальше: редактирование записей, напоминания о занятиях " +
    "и экспорт плана в календарь."),

  h1("Приложение. Пример файлов данных"),
  ...code(["exams.csv", "name,date,kind", "Математика,2026-11-02,exam", "Контрольная · Физика,2026-10-24,control", "",
    "topics.csv", "exam,name,difficulty,status,planned_day", "Математика,Пределы,5,done,2026-10-17", "Математика,Ряды,5,todo,2026-10-17", "",
    "settings.csv", "key,value", "daily_limit,4", "max_chunk,2"]),
];

const doc = new Document({
  creator: "Проект №60",
  title: "Отчёт: Планировщик подготовки к экзаменам",
  features: { updateFields: true },
  styles: {
    default: { document: { run: { font: FONT, size: 28 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: FONT }, paragraph: { spacing: { before: 360, after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: FONT }, paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [{ reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "–", alignment: AlignmentType.LEFT,
    style: { paragraph: { indent: { left: 1069, hanging: 360 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1701, right: 850 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 24 })] })] }) },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(OUT, buf); console.log("written", OUT); });
