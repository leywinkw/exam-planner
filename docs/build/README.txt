Пересборка презентации, отчёта и архива для сдачи (после добавления скриншотов в docs/screens):

  cd docs/build
  NODE_PATH=<папка с node_modules, где стоят pptxgenjs и docx> node build_deck.js
  NODE_PATH=<та же папка> node build_report.js
  cd ../..
  python3 docs/build/build_submission.py

Библиотеки ставятся один раз:  npm install pptxgenjs docx  (в любой служебной папке).
