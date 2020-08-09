import os
import re
import pandas as pd
import numpy as np
from natsort import natsorted, index_natsorted, order_by_index

part_pattern = "(^|ст(\.|))\s*\d{3}(\.\d{1}|)(\s*ч*\.*\s*\d{1}|)(\s*\.\d{1}|)"

def dropFirstRows(df, value2search, rowsNum = None):
    """
    Функция находит строку первого столбца в таблице, значение которой соответствует параметру value2search,
    и удаляет количество строк, указанное в параметре rowsNum. 
    Если rowsNum не задан - удаляются все строки начиная с самой верхней.
    """
    for index, val in df.iloc[:,0].str.contains(value2search).iteritems():
        if val == True and val != np.nan and index !=0:
            if rowsNum is None:
                df.drop(df.index[0:index], inplace=True)
            else:
                df.drop(df.index[index-rowsNum:index], inplace=True)
                break
            df.reset_index(drop=True, inplace=True)
    return df

def cutNumbers(string):
    '''Служебная функция нужная, чтобы при склеивании строк в tackleMergedCells вырезать строки, содержащие только числа'''
    string = str(string)
    string = string.replace("nan", "")
    match = re.search(r'(^\d+$)', string)
    if match:
        string = string.replace(match.group(), "")
    return string

def tackleMergedCells(df):
    if df.iloc[0:1].isnull().values.any():
        df.iloc[0:1].fillna(method='ffill', axis='columns', inplace=True)
        df.iloc[0:2].replace(to_replace=['\n', '-', '\*', '\s{3}', '\s{2}'],value=[' ', '', '', ' ', ' '], regex=True, inplace=True)
        for i in range(2, len(df.iloc[0])): # 2 - это номер колонки, с которой начинается смерживание объединенных колонок
            df.at[0, i] = str(df.iloc[0][i]).replace("nan", "") + " " + cutNumbers(df.iloc[1][i]) + " " + cutNumbers(df.iloc[2][i])
    else:
        df.iloc[0, ].replace(to_replace=['\n', '-', '\*', '\s{3}', '\s{2}'],value=[' ', '', '', ' ', ' '], regex=True, inplace=True)

    df.columns = pd.Series(df.iloc[0,]).str.strip()
    df.reset_index(drop=True, inplace=True)
    return df

def deleteUnusedCols(df, year):
    """
    Удаляет пустые колонки, а также неиспользуемые нами колонки 
    """
    df.dropna(axis='columns', how='all', inplace=True) # удаляем пустые колонки
    df.columns = pd.Series(df.iloc[0,]).astype('str') # превращаем первую строку в заголовок таблицы
    df = cleanСolsNames(df)
    
    indeces2remove = []
    
    # находим номер колонки, в которой содержится ненужный нам номер строки или пункта, если они попали в заголовок таблицы
    i = -1
    for col in df.columns:
        i += 1
        if col.find('№') > -1:
            indeces2remove.append(i)
            break
    # или находим номер колонки, в которой содержится ненужный нам номер строки или пункта, если они не попали в заголовок и отличаются от других колонок двумя строками с NA
    header_rows = 3 if year in [2017, 2018, 2019] else 2 # в 2017 и далее смерженные ячейки простираются на три строки, а не на две, как раньше
    j = -1
    for index, col in df.iloc[0:header_rows].iteritems():
        j += 1
        if col.isnull().values.all():
            indeces2remove.append(j)
        
    # удаляем колонку с найденным индексом 
    column_numbers = [x for x in range(df.shape[1])]  # list of columns' integer indices
    for index in indeces2remove:
        column_numbers.remove(index) #removing column integer index i
    df = df.iloc[:, column_numbers]
    df.columns = range(df.shape[1])
    return df
   
def cleanСolsNames(df):
    '''Очищает заголовок таблицы символов перевода строки, двоеточий, переводит заглавные буквы в строчные'''
    df.columns = df.columns.str.strip()
    df.columns = df.columns.str.lower()
    df.columns = df.columns.str.replace("\n", "")
    df.columns = df.columns.str.replace(":", "")
    return df

def renameColumns(df, columns2eng):
    for col in columns2eng.columns:
        for col2 in df.columns:
            if columns2eng[col].isin([col2]).any():
#                 print(col, col2)
#                 print('--------------')
                df.rename(index=str, columns={col2: col}, inplace=True)
    # проверяем, что все колонки переименовались
    for column in df.columns:
        if re.search(r'[а-яА-Я]', str(column)):
            print(column)
    return df

def dropNARows(df):
    df.drop(df.index[0:1], inplace=True)
    df.dropna(axis='rows', how='any', inplace=True)
    return df

def deleteUselessRows(df, year):
    '''Удаляем строки, в которых нет информации о конкретных статьях'''
    df['clause'] = df['clause'].astype(str)
    '''но сначала переименуем "Резервная строка по разделу VIII "Преступления в сфере экономики" УК РФ 
    (для составов преступлений, введенных в УК РФ после утверждения формы отчетности приказом № 130 от 28 июня 2013 г. )"
    в 185.6 ч.1-2
    '''
    if year == 2013:
        if 'totalConvicted' in df.columns or 'primaryImprisonment1' in df.columns:
            ind = df.index[df['clause'].str.contains('Резервная строка по разделу VIII "Преступления в сфере экономики" УК РФ')][0]
            df.at[ind, 'clause'] = '185.6 ч.1-2'
        #df['clause'] = df['clause'].str.replace('Резервная строка по разделу VIII "Преступления в сфере экономики" УК РФ \(для составов преступлений, введенных в УК РФ после утверждения формы отчетности приказом № 130 от 28 июня 2013 г\. \)', '185.6 ч.1-2')
        #df['clause'] = df['clause'].str.replace('Резервная строка по разделу VIII "Преступления в сфере экономики" УК РФ \(для составов преступлений, введенных в УК РФ после утверждения формы отчетности приказом № 130 от \)', '185.6 ч.1-2')
    df = df[~df['clause'].str.contains('пустая|Небольшой тяжести|Средней тяжести|Тяжкие|Особо тяжкие|Декриминализация|Преступления, введенные в УК РФ после утверждения форм отчетности приказом № 115|Составы преступлений, введенные в УК РФ после утверждения форм отчетности приказом № 130|Составы преступлений, введенные в УК РФ после утверждения форм отчетности приказом № $|283.1;\s*303\s*ч.4;\s*330.1|170.2 ч. 1; 170.2 ч. 2|284.1 ; 293 ч. 1.1|[Рр]езервная строка|204.1\. $|Сумма|Составы преступлений,\s*введенные в УК РФ в 201[89] году')]
    
    if 'name' in df.columns:
        df = df[~df['name'].str.contains('ВСЕГО|ИТОГО')]
    df = df.reset_index(drop=True) 
    return df

def insertEmptyRows(df, year, clauses2Insert):
    '''Поскольку в 2012 и 2015 годах встречаются строки, в которых собраны несколько статей, все значения по которым равны
    нулю, т.е. не было ни осужденных, ни прекращенных дел, ни оправданных и т.д., то такие строки можно разбить по статьям
    '''
    year = str(year)
    dict2Insert = {}
    if year in clauses2Insert.keys():
        for clause in clauses2Insert[year]:
            for col in df.columns:
                dict2Insert[col] = [0]
            dict2Insert['clause'] = clause
            df2Insert = pd.DataFrame.from_dict(dict2Insert)
            df_concat = pd.concat([df, df2Insert], sort=True)
            df = df_concat.reset_index(drop=True)
    return df

def fix204In2016(df, year):
    if year == 2016:
        ind = df.index[df['clause'] == '204.2. '][0]
        df.at[ind, 'clause'] = '204.2 ч. 1'
        
        ind = df.index[df['clause'] == '204.1 ч. 1'][0]
        df.at[ind, 'totalConvicted'] = 1
        df.at[ind, 'primaryFine'] = 1
        
        ind = df.index[df['clause'] == '204.1 ч. 2'][0]
        df.at[ind, 'totalConvicted'] = 2
        df.at[ind, 'primarySuspended'] = 1
        df.at[ind, 'primaryFine'] = 1
        df.at[ind, 'addFine'] = 1
    return df

def cleanClauseCol(df):
    df['clause'] = df['clause'].str.replace("Составы преступлений, введенные в УК РФ после утверждения форм отчетности:\nКлевета \(введ. ФЗ от 28.07.2012 N 141-ФЗ\) ст. ", "")
    df['clause'] = df['clause'].str.replace("Составы преступлений, введенные в раздел IX \"Преступления против общественной безопасности и общественного порядка\" УК РФ после утверждения форм отчетности приказом № 127\s+ст. ", "")
    df['clause'] = df['clause'].str.replace("Клевета в отношении судьи, присяжного заседателя, прокурора, следователя, лица, производящего дознание, судебного пристава \(введ. ФЗ от 28.07.2012 N 141-ФЗ\)\s+ст. ", "")
    
    df['clause'] = df['clause'].str.replace('Мошенничество, совершенное в сфере кредитования; при получении выплат; с использованием платежных карт; в сфере предпринимательской деят-ти; в сфере страхования; в сфере компьютерной информации \(введ. ФЗ от 29.11.2012 N 207-ФЗ\) ст\. ', '')
    
    df['clause'] = df['clause'].astype("str")
    df['clause'] = df['clause'].str.replace(" ", "")
    df['clause'] = df['clause'].str.replace("-", ".")
    df['clause'] = df['clause'].str.replace("ст(\.|)", "")
    df['clause'] = df['clause'].str.replace("\.ч", "ч")
    
    df['clause'] = df['clause'].str.replace("207\(.+\),", "")
    return df

def clauses2column(df):
    # создаем колонку part с номером статьи и части без примечаний и удаляем из нее лишние пробелы
    # df['clause'] = df['clause'].str.replace("\.\s*ч", "ч")
    # df['part'] = df.apply(lambda row: re.search(part_pattern, row['clause']).group(), axis=1)
    # на случай, если все-таки захочется вернуть воинские преступления
    df['part'] = df.apply(lambda row: re.search(part_pattern, row['clause']).group() if re.search(r'[Вв]оинск', row['clause']) is None else "Воинские преступления", axis=1)
    df['part'] = df['part'].str.replace("^ст\.\s", "")
    df['part'] = df['part'].str.replace(" ", "")
    # тут мы отрезаем номер статьи от примечаний типа "в старой редакции" - может пригодиться для целей сверки таблиц, но в целом нет
    '''
    df['clause'] = df.apply(lambda row: row['clause'].replace(re.search(part_pattern, row['clause']).group(), ""), axis=1)
    df['clause'] = df['clause'].str.replace("\sст. $", "")
    df['clause'] = df['clause'].str.replace("^\s", "")
    # колонку clause переименовываем в comments
    df.rename(index=str, columns={"clause": "comments"}, inplace=True)
    '''
    # в колонку clause складываем статьи без частей, используя ранее созданную колонку part
    df['clause'] = df.apply(lambda row: re.search(r'(\d{3}(\.\d{1}|))', row['part']).group() if re.search(r'[Вв]оинск', row['clause']) is None else "Воинские преступления", axis=1)
    #df['clause'] = df.apply(lambda row: re.search(r'(\d{3}(\.\d{1}|))', row['part']).group(), axis=1)
    df.replace("Воинскиепреступления", "Воинские преступления", inplace=True)
    return df

def addMilitaryOfences(df):
    df = pd.concat([df, pd.DataFrame([[np.nan] * df.shape[1]], columns=df.columns)], ignore_index=True)
    ind = np.where(df['name'].isna())[0][0]
    df.at[ind, 'name'] = "Воинские преступления"
    df.at[ind, 'clause'] = "Воинские преступления"
    df.at[ind, 'part'] = "Воинские преступления"
    return df

def rearrangeCols(df, firstCols):
    cols = firstCols  + [col for col in df.columns.tolist() if col not in firstCols]
    df = df[cols]
    return df

def sortTable(df):
    '''Сортирует таблицу по колонке part - со статьей и часть методом натуральной сортировки'''
    df = df.reindex(index=order_by_index(df.index, index_natsorted(df['part'])))
    df = df.reset_index(drop=True)
    return df

def keepCombinedRows(df, year):
    if year == 2012:
        df['clause'] = df['clause'].str.replace('159.1', '159.1-159.6')
        df['part'] = df['part'].str.replace('159.1.1', '159.1-159.6')
    if year == 2013:
        df['part'] = df['part'].str.replace('185.6ч.1.2', '185.6ч.1-2')
    if year == 2016:
        df['part'] = df['part'].str.replace('204ч.5', '204ч.5,ч.6,ч.7,ч.8')
        df['part'] = df['part'].str.replace('159ч.5', '159ч.5,ч.6,ч.7')
    return df

def solveProblem2012(df, year):
    if year == 2012:
        df['clause'] =  df['clause'].str.replace("^133$", "133ч.1")
    return df

def solveProblem2013_2014(df, year):
    if year == 2013 or year == 2014:
        df['part'] =  df['part'].str.replace("^136$", "136ч.2")
    return df


def nameSeparatedRows(df, names):
    for key in names.keys():
        ind = df.index[df['part'] == key].tolist()
        if len(ind) == 1:
            df.at[ind[0], 'name'] = names[key]
    return df

def meltTable(df, year):
    '''Приводит таблицу в длинную форму'''
    df.insert(0, 'year', [year]*len(df))
    df = pd.melt(df, id_vars=['year', 'clause', 'part', 'name'], value_vars = list(df.columns)[4:], var_name='parameter', value_name='value')
    return df

# Проверочные функции

def checkTablesLen(main, add, parameters = None):
    if parameters is not None:
        if len(main) != len(parameters):
            print("Не ОК: длины таблиц № 10.3 и № 10.3.1 не совпадают")
        else:
            print("ОК: длины таблиц № 10.3 и № 10.3.1 совпадают")
    if len(main) != len(add): 
        print("Не ОК: длины таблиц № 10.3 и № 10-а не совпадают")
    else:
        print("ОК: длины таблиц № 10.3 и № 10-а совпадают")
        
def checkNumbersBetweenForms(year, mainDF, addDF, parametersDF = None):
    if year > 2010:
        for i in range(len(mainDF)):
            if mainDF.iloc[i]['part'] != parametersDF.iloc[i]['part']:
                print(i, "main", mainDF.iloc[i]['part'], "parameters", parametersDF.iloc[i]['part'])

            imprisonment_sum = parametersDF.iloc[i]['primaryImprisonment1'] + \
                                                         parametersDF.iloc[i]['primaryImprisonment1_2'] + \
                                                         parametersDF.iloc[i]['primaryImprisonment2_3'] + \
                                                         parametersDF.iloc[i]['primaryImprisonment3_5'] +\
                                                         parametersDF.iloc[i]['primaryImprisonment5_8'] +\
                                                         parametersDF.iloc[i]['primaryImprisonment8_10'] +\
                                                         parametersDF.iloc[i]['primaryImprisonment10_15'] +\
                                                         parametersDF.iloc[i]['primaryImprisonment15_20']
            if mainDF.iloc[i]['primaryImprisonment'] != imprisonment_sum:
                print("Не совпадает число осужденных к лишению свободы.", "\nСтатья: ", mainDF.iloc[i]['part'], "\n10.3", "Лишение свободы всего: ", mainDF.iloc[i]['primaryImprisonment'], 
                      "\n10.3.1", "Лишение свободы сумма: ", imprisonment_sum)

            if mainDF.iloc[i]['part'] != addDF.iloc[i]['part']:
                print("Не совпадают номера статей. 10.3:", mainDF.iloc[i]['part'], "10-a:", addDF.iloc[i]['part'], "Год: ", year)
            if mainDF.iloc[i]['totalConvicted'] != addDF.iloc[i]['totalConvictedMain']:
                print("Не совпадает число осужденных по основной статье.", "\nСтатья: ", mainDF.iloc[i]['part'], "\n10.3:", mainDF.iloc[i]['totalConvicted'], "\n10-a:", addDF.iloc[i]['totalConvictedMain'], "\nГод:", year)
    else:
        for i in range(len(mainDF)):
            if mainDF.iloc[i]['part'] != addDF.iloc[i]['part']:
                print("Не совпадают номера статей. 10.3:", mainDF.iloc[i]['part'], "10-a:", addDF.iloc[i]['part'], "Год: ", year)
            if mainDF.iloc[i]['totalConvicted'] != addDF.iloc[i]['totalConvictedMain']:
                print("Не совпадает число осужденных по основной статье.", "\nСтатья: ", mainDF.iloc[i]['part'], "\n10.3:", mainDF.iloc[i]['totalConvicted'], "\n10-a:", addDF.iloc[i]['totalConvictedMain'], "\nГод:", year)
                
def compareSums(df, columns, total_values, start):
    columns = list(columns)[start:]
    cols = [col for col in columns if not re.search(r'[а-яА-Я]', col)]
    values2remove = []
    for col in columns:
        match = re.search(r'[а-яА-Я]{2,}', col)
        if match:
            ind = columns.index(col)
            values2remove.append(total_values[ind])
    values = [val for val in total_values if val not in values2remove]
    total_values = values
    DFreordered = df[cols]
    sums = DFreordered.sum(axis='index')
#     print(sums)
    if len(total_values) != len(sums):
        print("Количество колонок не совпадает")
    for i in range(0, len(total_values)):
        if total_values[i] != sums[i]:
            print('\nСумма значений в колонке', DFreordered.columns[i], sums[i], '\n', 'Значение в строке "Всего по составам УК РФ" ', total_values[i])