from django.apps import apps

from PyPDF2 import PdfReader
import pdfplumber

import json
from fuzzywuzzy import fuzz

import requests
import json
import re
from nltk.stem import SnowballStemmer
import nltk

nltk.download('punkt')

def clean_text(text):
    """Очистка текста от лишних пробелов и символов."""
    text = re.sub(r' +', ' ', text)       # Удаляем лишние пробелы
    cleaned_text = re.sub(r'\s+([.,;:!?\-)])', r'\1', text)
    return cleaned_text.strip()

def extract_diagnoses(text):
    """Извлечение диагнозов из текста."""
    # Регулярное выражение для поиска кодов диагнозов и их описаний
    diagnosis_pattern = re.compile(
        r"([A-ZА-Я]\d{2}\.*\d{0,2}\.*)\s+([^;,.]+(?:\s*\.\s*[^\s]*)?)|"  # Код диагноза с описанием
        r"([^;,.]+)"  # Описание диагноза без кода
    )

    # Ищем текст после ключевого слова "Диагноз" до конца абзаца
    diagnosis_paragraph_pattern = re.compile(
        r"Диагноз(?:\s+[\w\-]+)*\s*:\s*(.*?)(?=\n|$)",  # Захватываем текст после "Диагноз" до конца абзаца
        re.IGNORECASE | re.DOTALL  # Учитываем многострочный текст
    )

    match = diagnosis_paragraph_pattern.search(text)
    if match:
        text = match.group(1).strip()
        text = re.sub(r'\s+', ' ', text)
        text = text.rstrip(';')
        text = text.rstrip('.')

    # Разделяем текст на части по допустимым разделителям (; или ,)
    parts = re.split(r"[;,]", text)

    diagnoses = []

    for part in parts:
        part = part.strip()  # Убираем лишние пробелы
        match = diagnosis_pattern.search(part)  # Поиск как с кодом, так и без
        if match:
            if match.group(1):  # Если есть код
                diagnoses.append({
                    "code": match.group(1),  # Код диагноза
                    "description": match.group(2).strip() if match.group(2) else ''  # Описание диагноза
                })
            else:  # Если нет кода
                diagnoses.append({
                    "code": None,  # Указываем, что кода нет
                    "description": match.group(3).strip()  # Описание диагноза
                })

    return diagnoses

def extract_analyses(text):
    analysis_pattern = re.compile(
        r"(?:анализ(?:ы)?|исследование(?:я)?)(?:\s+[\w\-]+)*\s*:\s*(.*?)(?=\n|$)",
        re.IGNORECASE | re.DOTALL  # Игнорируем регистр
    )
    
    matches = analysis_pattern.findall(text)
    analysis_data = []
    for match in matches:
        cleaned_values = re.sub(r'^(?:.*?)(?=\b\w{4,}\b)', '', match)
        pattern = re.compile(r'(\b[А-Яа-яA-Za-z]+\b(?:\s+[А-Яа-яA-Za-z]+)*)[:\s]*([\d.,]+)', re.UNICODE)
        matches_analyses = pattern.findall(cleaned_values)
        analyses_data = [{"parameter": process_string(match[0].strip()), "value": normalize_value(match[1].strip()), 'description': analyze_test_result(process_string(match[0].strip()), normalize_value(match[1].strip()))} for match in matches_analyses]
        analysis_data.append(analyses_data)
    return analysis_data

def extract_diagnoses_and_analyses(text):
    diagnoses = extract_diagnoses(text)
    analyses = extract_analyses(text)
    return diagnoses, analyses


def get_json_data(name):
    """
    Возвращает загруженные данные из JSON, хранящиеся в AppConfig.
    """
    app_config = apps.get_app_config("site_form")  # Укажите имя вашего приложения
    if name == "disease_data" and hasattr(app_config, "disease_data") and app_config.disease_data:
        return app_config.disease_data
    elif name == "analyses_data" and hasattr(app_config, "analyses_data") and app_config.analyses_data:
        return app_config.analyses_data
    else:
        raise ValueError("JSON данные не загружены или отсутствуют.")
    
def collect_diseases_status(queries):
    """
    Формирует список diseases из анализируемых данных.

    :param data: Список заболеваний в формате [{keyword, status}, ...].
    :param queries: Список строк с диагнозами для анализа.
    :return: Сформированный список diseases.
    """
    data = get_json_data("disease_data")
    diseases = []

    for query in queries:
        results = find_potential_status(data, query['description'])  # Используем find_potential_status
        #print(results)
        for result in results:
            if "status" in result:  # Если статус найден
                diseases.append({
                    "keyword": query['description'],  # Ключевые слова
                    "description": result["description"], # Статус
                    "status": result["status"]  # Статус
                })
            else:
                diseases.append({
                    "keyword": query['description'],
                    "status": "Статус не найден"  # Если ничего не найдено
                })

    return diseases


def stem_words(words):
    """Функция для стемминга слов."""
    stemmer = SnowballStemmer("russian")
    return {stemmer.stem(word) if len(word) > 5 else word for word in words}

def find_potential_status(diseases, query, threshold=95):
    best_matches = []  # Список лучших совпадений
    best_percentage = 0
    ignored_word = ['степен']

    # Приводим запрос к нижнему регистру для сравнения и фильтруем слова длиной более 2 символов
    query_lower = query.lower()
    query_words = set(word for word in query_lower.split() if len(word) > 2)  # Слова длиной более 2 символов
    query_stems = stem_words(query_words)  # Стемминг слов запроса
    print(query_stems)

    for disease_name, details in diseases.items():
        # Приводим названия заболеваний и описания к нижнему регистру
        disease_name_lower = disease_name.lower()
        description_lower = details['Description'].lower()

        # Разбиваем ключевые слова заболевания на уникальные слова
        keywords = set(word for word in disease_name_lower.split() + description_lower.split() if len(word) > 2)
        keywords_stems = stem_words(keywords)  # Стемминг ключевых слов

        if not keywords:
            continue  # Пропускаем, если нет ключевых слов

        matched_keywords = []
        # Считаем количество совпадений
        for query_word in query_stems:
            if query_word in ignored_word:
                continue

            for keyword in keywords_stems:
                # Используем token_sort_ratio для первичного сопоставления
                match_percentage = fuzz.token_sort_ratio(query_word, keyword)

                def has_sbstr():
                    for i in range(len(query_word), 0, -1):  # Сокращаем слово от конца
                        substring = query_word[:i]  # Получаем подстроку
                        if substring in keyword and len(substring) > len(query_word) / 2:
                            matched_keywords.append(keyword)
                            return True
                        return False

                if match_percentage >= threshold and not len(query_word) < len(keyword) and has_sbstr():
                    break;  # Если совпадение выше порога

        match_percentage = len(matched_keywords) / len(query_words) * 100

        if match_percentage > best_percentage and  match_percentage > 0:
            best_matches = [{
                'keyword': disease_name,
                'description':  disease_name_lower + ' ' +  description_lower,
                'status': details['Статус'].split(',')[0],
                'matched_keywords': list(matched_keywords),
                'match_percentage': match_percentage
            }]
            best_percentage = match_percentage
        elif match_percentage == best_percentage and match_percentage > 0:
            best_matches.append({
                'keyword': disease_name,
                'description': disease_name_lower + ' ' + description_lower,
                'status': details['Статус'].split(',')[0],
                'matched_keywords': list(matched_keywords),
                'match_percentage': match_percentage
            })

    if best_matches:
        return best_matches
    else:
        return {"message": "Статус не найден. Попробуйте уточнить диагноз."}

def extract_text_from_pdf(pdf_file):
    """
    Извлечение текста из PDF-файла.
    """
    reader = PdfReader(pdf_file)  # Открываем файл
    text = ""

    for page in reader.pages:  # Проходим по всем страницам
        text += page.extract_text()  # Извлекаем текст из каждой страницы
    
    return replace_newlines(text)

def extract_tables_from_pdf(pdf_file):
    """
    Извлечение таблиц из PDF-файла.
    :param pdf_file: Путь к файлу PDF или объект файла.
    :return: Список таблиц (каждая таблица — список списков).
    """
    tables = []
    with pdfplumber.open(pdf_file) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            table = page.extract_table()  # Извлекаем таблицу с текущей страницы
            if table:
                print(f"Таблица найдена на странице {page_number}")
                tables.append(table)
                print(table)
    return tables

def replace_newlines(text):
    """
    Заменяет переносы строк \n на пробелы, если после них не следует заглавная буква или цифра.
    """
    # Заменяем \n на пробел, если после него не следует заглавная буква или цифра
    modified_text = re.sub(r'\n\s*(?=[^А-Я])', ' ', text)
    modified_text = re.sub(r'(?<=\d)\s*\n', ' ', modified_text)
    return clean_text(modified_text)

def normalize_value(raw_value):
    """
    Приводит значение к числовому формату (float).
    
    :param raw_value: Значение в формате строки, извлечённое из PDF.
    :return: Числовое значение (float) или None, если значение некорректно.
    """
    try:
        # Удаляем лишние символы и заменяем запятые на точки
        clean_value = re.sub(r'[^\d,.-]', '', raw_value).replace(',', '.')
        clean_value = re.sub(r'^\.+|\.+$', '', clean_value)
        
        # Если значение имеет больше одной точки/запятой, оно некорректно
        if clean_value.count('.') > 1:
            print(clean_value)
            return None
        
        # Преобразуем в число
        return float(clean_value)
    except ValueError:
        # Если преобразование не удалось
        print(raw_value)
        return None

# Проверка попадания в нормальный диапазон
def is_within_range(value, normal_range):
    """
    Проверяет, находится ли значение в нормальном диапазоне.

    :param value: Числовое значение анализа.
    :param normal_range: Строка или словарь с нормальным диапазоном.
    :return: True, если значение в пределах нормы.
    """
    if value is None:
        return False

    if isinstance(normal_range, str):  # Пример: "66-83"
        try:
            if re.search('-', normal_range):
                min_val, max_val = map(float, normal_range.split('-'))
                return min_val <= value <= max_val
            elif normal_range.startswith('<'):
                # В случае "<83" мы проверяем, что значение меньше 83
                max_val = float(normal_range[1:])
                return value < max_val
            elif normal_range.startswith('>'):
                # В случае ">53" мы проверяем, что значение больше 53
                min_val = float(normal_range[1:])
                return value > min_val
        except ValueError:
            return False
    elif isinstance(normal_range, dict):  # Пример: {"женщины": "53-97"}
        # Здесь можно добавить логику для выбора диапазона по полу/возрасту
        return False
    return False

# Основная функция анализа
def analyze_test_result(test_name, test_value):
    """
    Анализирует значение анализа на соответствие норме.

    :param test_name: Название анализа, извлечённое из PDF.
    :param test_value: Значение анализа.
    :return: Результат анализа.
    """
    tests_data = get_json_data("analyses_data")

    # Поиск анализа по названию
    best_match = None
    best_similarity = 0

    # Поиск наилучшего совпадения
    for test in tests_data['tests']:
        # Проверяем схожесть названия анализа
        similarity = fuzz.token_set_ratio(test_name.lower(), test["name"].lower())
        if similarity > best_similarity:  # Сохраняем наилучшее совпадение
            best_match = test
            best_similarity = similarity

    # Проверка наилучшего совпадения
    if best_match and best_similarity >= 30:
        # Получаем диапазон и проверяем значение
        normal_range = best_match["normal_range"]
        if is_within_range(test_value, normal_range):
            return (f"{best_match['name']} ({test_value}) находится в пределах нормы ({normal_range}).")
        else:
            return (f"{best_match['name']} ({test_value}) выходит за пределы нормы ({normal_range}). Описание: {best_match['description']}")
    else:
        return (f"'{test_name}' не найдено в списке анализов или совпадение недостаточное (лучшее совпадение: {best_similarity}%).")

def process_string(input_string):
    """
    Если в строке больше одной заглавной буквы, 
    удаляет все пробелы и разделяет строку по заглавным буквам.
    """
    # Находим количество заглавных букв
    uppercase_count = sum(1 for char in input_string if char.isupper())

    if uppercase_count > 1:
        # Удаляем все пробелы из строки
        input_string_no_spaces = input_string.replace(" ", "")
        # Разделяем строку по заглавным буквам, не разделяя последовательные заглавные буквы
        abbreviation_pattern = re.compile(r'\b[A-ZА-Я]{2,}(?:\.[A-ZА-Я]{2,})*\b')
        abbreviations = abbreviation_pattern.findall(input_string)
        input_string_no_spaces = re.sub(abbreviation_pattern, '', input_string_no_spaces)
        parts = list
        parts = re.findall(r'[A-ZА-Я][a-zа-я]*|[A-ZА-Я]+(?=[A-ZА-Я]|$)', input_string_no_spaces)
        parts.extend(abbreviations)
        
        return ' '.join(parts)
    else:
        return input_string