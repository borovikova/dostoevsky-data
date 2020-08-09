# Код обработки данных для проекта Достоевский

### Содержимое репозитория

`ExcelFiles` - исходные файлы

`computational_essay_2009-2018.ipynb` - обработка данных за 2009-2018 года
`computational_essay_2019.ipynb` - обработка ланных за 2019 год
`tools.py` - вспомогальный код

Вспомогательные файлы для переименовывания столбцов:
`colNames2engNames.csv`
`colNames2engNamesAdd.csv`
`colNames2engNamesParameters.csv`

`metrics.json` - сопоставление названий столбцов на латинице с кириллическими названиями

### Как установить

Предполагается, что Python3 и Jupyter Notebook уже установлены.

Для работы понадобятся pandas, natsort, xlrd. Чтобы установить все сразу, используйте `requirements.txt`
```
pip install -r requirements.txt
```
