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
  center("(проект № 60)", { size: 28, after: 2400 }),
  new Paragraph({ alignment: AlignmentType.RIGHT, spacing: { after: 80 }, children: [run("Выполнил: [ФИО]")] }),
  new Paragraph({ alignment: AlignmentType.RIGHT, spacing: { after: 80 }, children: [run("Группа: [номер группы]")] }),
  new Paragraph({ alignment: AlignmentType.RIGHT, spacing: { after: 1800 }, children: [run("Проверил: [ФИО преподавателя]")] }),
  center("2026", { size: 28 }),
  new Paragraph({ children: [new PageBreak()] }),
  center("СОДЕРЖАНИЕ", { size: 32, bold: true, after: 200 }),
  new TableOfContents("Содержание", { hyperlink: true, headingStyleRange: "1-2" }),
  new Paragraph({ children: [new PageBreak()] }),
];

const children = [
  ...title,

  h1("1. Постановка задачи"),
  body("Цель проекта — разработать программу, которая помогает студенту подготовиться к экзаменам: пользователь вводит экзамены, " +
    "их даты и темы с оценкой сложности, а программа распределяет, что нужно учить в каждый день, и пересчитывает план, если пользователь отстаёт. " +
    "Результат должен быть показан наглядно — в виде диаграммы Ганта или календаря нагрузки."),
  body("Требования к проекту:"),
  bullet("язык Python, использование только материала, пройденного на курсе;"),
  bullet("обязательные инструменты: обработка ошибок, словари, объектно-ориентированное программирование (ООП);"),
  bullet("четвёртый критерий — визуализация (окно tkinter, график и т. п.);"),
  bullet("для хранения данных — база данных, а при её отсутствии — файлы CSV или словари."),
  body("Дополнительно к заданию реализованы контрольные работы (несколько тем на одну дату), автоматический подбор сложности темы, " +
    "выпадающие списки типовых предметов и тем, а также автоматические тесты."),

  h1("2. Используемые инструменты"),
  table(["Инструмент", "Для чего использован"], [
    ["Python 3", "основной язык программирования; проект работает на версии 3.9 и новее"],
    ["tkinter, ttk", "окно программы: формы, выпадающие списки, таблицы, вкладки, диалоги, календарь"],
    ["tkinter.Canvas", "рисование диаграммы Ганта"],
    ["модуль csv, pathlib", "хранение данных в файлах exams.csv, topics.csv, settings.csv"],
    ["datetime, calendar", "работа с датами, построение сетки календаря на месяц"],
    ["pytest", "автоматические тесты логики (70 тестов)"],
    ["git", "хранение истории изменений проекта"],
  ], [3000, 6355]),
  gap(),
  body("Сторонние пакеты для работы программы не нужны — используется только стандартная библиотека Python. " +
    "Пакет pytest нужен только для запуска тестов."),

  h1("3. Структура проекта"),
  body("Программа разделена на логику (папка planner) и интерфейс (папка ui). Логика ничего не знает про окно, поэтому её можно " +
    "проверять автоматическими тестами без запуска интерфейса."),
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
  body("Пользователь выбирает предмет из выпадающего списка (или вводит своё название), указывает дату в формате ДД.ММ.ГГГГ и тип события — " +
    "«Экзамен» или «Контрольная». У каждого события своя дата и свои темы. В списке событий показывается, сколько дней осталось. " +
    "Дата должна быть в будущем, название не может быть пустым, одинаковые события не допускаются."),
  h2("4.2. Темы и автоподбор сложности"),
  body("После выбора события в списке тем появляются типовые темы этого предмета; уже добавленные в список не попадают. " +
    "Тему можно ввести вручную, а кнопка «Несколько…» открывает окно, где можно отметить сразу много тем и дописать свои через запятую."),
  body("Сложность темы — число от 1 до 5, она же определяет число часов на тему. По умолчанию выбрано значение «авто»: программа определяет " +
    "сложность по названию предмета и темы с помощью словарей (например, математика — 4, физкультура — 1, слово «введение» уменьшает сложность, " +
    "слова «теорема» или «интеграл» увеличивают). Значение можно задать вручную или изменить у уже добавленной темы."),
  ...figure("03_dialog.png", "Окно добавления нескольких тем", 380),
  h2("4.3. Распределение по дням"),
  body("План строится автоматически после каждого изменения. Правила распределения:"),
  bullet("число часов на тему равно её сложности;"),
  bullet("в один день планируется не больше заданного числа часов (по умолчанию 4) и не больше 2 часов одной темы — поэтому большая тема " +
    "растягивается на несколько дней по 1–2 часа;"),
  bullet("первыми планируются самые сложные темы ближайшего по дате события;"),
  bullet("день перед экзаменом отводится на повторение (2 часа), перед контрольной — 1 час; в день события занятия не планируются;"),
  bullet("если темы не помещаются до срока, программа не перегружает дни, а предупреждает, какие темы под угрозой."),
  h2("4.4. Пересчёт плана"),
  body("Если пользователь отстаёт, он нажимает «Перепланировать». Для каждой темы запоминается день, на который она была запланирована. " +
    "Невыполненные темы, день которых уже прошёл, планируются заново, начиная с сегодняшнего дня; программа показывает, что было перенесено, " +
    "и предупреждает о темах, которые уже не помещаются. Выполненные темы отмечаются кнопкой «Готово» и в плане больше не участвуют."),
  h2("4.5. Визуализация"),
  body("Календарь нагрузки показывает месяц; цвет клетки отражает загрузку дня (от серого — свободно до оранжевого — лимит часов), " +
    "экзамены отмечены красным, контрольные — фиолетовым. По щелчку на день внизу показываются темы этого дня и часы."),
  ...figure("01_calendar.png", "Календарь нагрузки", 560),
  body("Диаграмма Ганта нарисована на tkinter Canvas: каждая тема — полоска от первого до последнего дня занятий, полоски сгруппированы по " +
    "событиям. Вертикальные линии отмечают даты экзаменов и контрольных, пунктирная линия — сегодняшний день. Выполненные темы и темы, " +
    "которые не помещаются до срока, показаны отдельными строками."),
  ...figure("02_gantt.png", "Диаграмма Ганта", 560),
  h2("4.6. Хранение данных"),
  body("Данные сохраняются автоматически после каждого изменения в три CSV-файла папки data: exams.csv (события), topics.csv (темы) и " +
    "settings.csv (лимиты часов). Файлы записываются через временный файл, поэтому сбой не оставит наполовину записанный файл. " +
    "Если файл повреждён, программа не падает: она переименовывает его в .bak, сообщает об этом пользователю и начинает с пустого плана."),

  h1("5. Описание методов и алгоритмов"),
  h2("5.1. Классы и их методы"),
  table(["Класс / функция", "Назначение"], [
    ["Exam (models.py)", "экзамен или контрольная: название, дата, тип; проверяет корректность данных"],
    ["Topic (models.py)", "тема: событие, название, сложность 1–5, статус, день планирования; свойство hours — часы"],
    ["parse_date, parse_difficulty, clean_name", "проверка и преобразование введённых значений; при ошибке выбрасывают ValidationError"],
    ["Planner.add_exam, add_topic", "добавление события и темы с проверками (дата в будущем, повторы, существование события)"],
    ["Planner.remove_exam, remove_topic", "удаление события вместе с его темами / удаление темы"],
    ["Planner.set_difficulty, set_status", "изменение сложности темы (в том числе «авто») и статуса «готово»"],
    ["Planner.set_daily_limit, set_max_chunk", "лимит часов в день и часов одной темы в день с проверкой диапазона"],
    ["Planner.build_plan", "строит словарь плана {дата: [(событие, тема, часы)]}; возвращает темы, не поместившиеся в срок"],
    ["Planner.replan", "находит пропущенные темы, строит план заново и возвращает (перенесённые, под угрозой)"],
    ["Planner.day_load", "сумма часов за день — для цвета в календаре"],
    ["estimate_difficulty (estimator.py)", "сложность по названию предмета и темы с помощью словарей основ и поправок"],
    ["subjects, topics_for (catalog.py)", "списки предметов и типовых тем для выпадающих списков"],
    ["Storage.save, Storage.load", "запись и чтение CSV; при повреждении файлов — копия .bak и пустой план"],
    ["gantt_rows (ganttview.py)", "готовит строки диаграммы Ганта: период каждой темы, выполненные и не поместившиеся темы"],
    ["month_weeks, shift_month, load_color", "сетка месяца, переход между месяцами, цвет клетки по нагрузке"],
    ["App, GanttChart, MultiTopicDialog (ui)", "главное окно, диаграмма Ганта на Canvas, диалог выбора нескольких тем"],
    ["PlannerError, ValidationError, StorageError", "собственные исключения: ошибки ввода и ошибки работы с файлами"],
  ], [3600, 5755]),
  gap(),
  h2("5.2. Алгоритм построения плана"),
  body("Метод build_plan работает по шагам. Сначала собирается множество закрытых дней — дни событий и дни перед ними. " +
    "Затем на день перед каждым событием ставится повторение. После этого события обходятся по возрастанию даты, " +
    "а темы каждого события — по убыванию сложности. Для каждой темы перебираются дни от сегодняшнего до последнего учебного дня " +
    "(за два дня до события); в свободный день ставится порция часов, не больше свободного места в дне и не больше лимита на тему в день. " +
    "Если часы кончились раньше срока, тема размещена; если нет — она добавляется в список «под угрозой»."),
  ...code([
    "закрытые_дни = даты событий и дни перед ними",
    "для каждого события: поставить повторение на день перед ним",
    "для события в порядке возрастания даты:",
    "    для темы в порядке убывания сложности:",
    "        осталось = часы темы",
    "        для дня от сегодня до (дата события - 2 дня):",
    "            если день не закрыт и в нём есть место:",
    "                порция = min(место в дне, осталось, лимит на тему)",
    "                поставить порцию в план; осталось -= порция",
    "        если осталось > 0: добавить тему в «под угрозой»",
  ]),
  body("План хранится в словаре: ключ — дата, значение — список кортежей (событие, тема, часы). " +
    "Такая структура удобна и для календаря (сумма часов по ключу), и для диаграммы (первый и последний день темы)."),
  h2("5.3. Автоподбор сложности"),
  body("Функция estimate_difficulty использует два словаря. В первом хранится базовая сложность предмета по основе слова " +
    "(«математ» — 4, «литератур» — 2, «физкультур» — 1); для неизвестного предмета берётся 3. Во втором — поправки по словам в названии темы " +
    "(«введени» — минус 2, «основ» — минус 1, «теорем» — плюс 1). Результат ограничивается диапазоном от 1 до 5."),
  h2("5.4. Обработка ошибок"),
  body("Все проверки ввода выбрасывают собственные исключения: ValidationError (неверная дата, пустое название, сложность вне диапазона, повтор) " +
    "и StorageError (ошибка записи файла); оба наследуются от PlannerError. В окне действия пользователя выполняются в блоке try, " +
    "а ошибка показывается понятным сообщением в диалоге — программа не завершается аварийно."),
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
  table(["Требование", "Как выполнено"], [
    ["Обработка ошибок", "собственные исключения, блоки try/except в окне и при работе с файлами, повреждённые файлы не ломают программу"],
    ["Словари", "план {дата: [занятия]}, словари основ предметов и поправок сложности, каталог предметов и тем, события и темы в словарях класса Planner"],
    ["ООП", "классы Exam, Topic, Planner, Storage, App, GanttChart, MultiTopicDialog, иерархия исключений"],
    ["Визуализация", "календарь нагрузки и диаграмма Ганта в окне tkinter"],
    ["Хранение данных", "файлы CSV (базы данных не использовались)"],
    ["Дополнительно", "автоматические тесты pytest, автоподбор сложности, контрольные работы, выпадающие списки"],
  ], [2800, 6555]),

  h1("7. Тестирование"),
  h2("7.1. Автоматические тесты"),
  body("Логика проверена 70 автоматическими тестами pytest (папка tests). Они охватывают: неверные даты, сложность и лимиты; " +
    "выполнение лимитов часов; день перед экзаменом только для повторения; распределение темы по дням; перепланирование; " +
    "автоподбор сложности; списки предметов; чтение и запись CSV, в том числе повреждённых, неполных файлов и файлов с BOM. " +
    "Запуск: pytest (результат — 70 passed)."),
  h2("7.2. Примеры ввода и вывода"),
  body("Ниже приведены реальные результаты работы программы (скрипт examples/io_demo.py с фиксированной датой «сегодня» — 01.10.2026)."),
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
  body("Построенный план для двух событий (экзамен по математике 11.10 и контрольная по физике 06.10; лимит 4 часа в день, не более 2 часов одной темы в день):"),
  ...code(planLines),
  body("Перепланирование через 3 дня (пользователь отстал):"),
  ...code(replanLines),
  ...figure("04_error.png", "Сообщение об ошибке при вводе неверной даты", 420),

  h1("8. Запуск программы"),
  ...code(["cd exam-planner", "python3 main.py"]),
  body("Для запуска нужен Python 3.9 или новее с модулем tkinter (входит в стандартную установку). Для запуска тестов: " +
    "создать виртуальное окружение, установить pytest и выполнить pytest. Окно с примерными данными для проверки: python3 demo.py."),

  h1("9. Заключение"),
  body("В ходе работы создан планировщик подготовки к экзаменам: программа принимает экзамены и контрольные с темами, автоматически подбирает " +
    "сложность, распределяет темы по дням с учётом лимитов, пересчитывает план при отставании и показывает результат в календаре нагрузки и на " +
    "диаграмме Ганта. Все обязательные требования курса (обработка ошибок, словари, ООП) и дополнительный критерий (визуализация) выполнены, " +
    "данные хранятся в CSV-файлах, логика покрыта автоматическими тестами. " +
    "Возможные направления развития: редактирование записей, уведомления о занятиях, экспорт плана в календарь."),

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
