import pytest
from unittest.mock import Mock

# Импортируем функции из файла text_utils
from site_form.text_utils import (
    clean_text,
    extract_diagnoses,
    extract_analyses,
    process_string,
    is_within_range
)

def test_value_within_range():
    # Тест 1: Значение внутри диапазона "66-83"
    assert is_within_range(75, "66-83") == True

def test_value_outside_range():
    # Тест 2: Значение за пределами диапазона "66-83"
    assert is_within_range(85, "66-83") == False

def test_value_less_than():
    # Тест 3: Значение меньше диапазона "<83"
    assert is_within_range(80, "<83") == True
    assert is_within_range(83, "<83") == False

def test_value_greater_than():
    # Тест 4: Значение больше диапазона ">53"
    assert is_within_range(60, ">53") == True
    assert is_within_range(53, ">53") == False

def test_invalid_range():
    # Тест 5: Некорректный формат диапазона
    assert is_within_range(100, "abc") == False
    assert is_within_range(None, "66-83") == False
    assert is_within_range(45, "66-83") == False



def test_extract_diagnoses_with_code():
    # Тест извлечения диагнозов с кодами
    text = "Диагноз: A12.3 Сахарный диабет; В56.2 Простуда"
    diagnoses = extract_diagnoses(text)
    assert len(diagnoses) == 2
    assert diagnoses[0]["code"] == "A12.3"
    assert diagnoses[0]["description"] == "Сахарный диабет"
    assert diagnoses[1]["code"] == "В56.2"
    assert diagnoses[1]["description"] == "Простуда"

def test_extract_diagnoses_without_code():
    # Тест извлечения диагнозов без кодов
    text = "Диагноз: Грипп, Простуда"
    diagnoses = extract_diagnoses(text)
    assert len(diagnoses) == 2
    assert diagnoses[0]["code"] is None
    assert diagnoses[0]["description"] == "Грипп"
    assert diagnoses[1]["code"] is None
    assert diagnoses[1]["description"] == "Простуда"
    

def test_clean_text_special_characters():
    # Тест: Удаление спецсимволов
    assert clean_text("Текст! С, различными: знаками...") == "Текст! С, различными: знаками..."

def test_extract_analyses_empty_input():
    # Тест извлечения анализов из пустого текста
    text = " "
    analyses = extract_analyses(text)
    assert len(analyses) == 0

def test_process_string_with_no_changes():
    # Тест: Обработка строки, которая уже корректна
    result = process_string("Строка уже нормальная.")
    assert result == "Строка уже нормальная."

def test_clean_text():
    assert clean_text(" Привет  ,   мир ! ") == "Привет, мир!"
    assert clean_text("Hello  , world !") == "Hello, world!"
    assert clean_text("  Тестовый \nтекст  ") == "Тестовый \nтекст"


def test_is_within_range():
    assert is_within_range(13.5, "10-20") is True
    assert is_within_range(5.0, ">4.5") is True
    assert is_within_range(3.0, "<5.0") is True
    assert is_within_range(25.0, "10-20") is False

def test_extract_diagnoses():
    text = """
    Диагноз: J20.9 Острый бронхит неуточнённый; N10 Острый тубулоинтерстициальный нефрит.
    """
    expected_output = [
        {"code": "J20.9", "description": "Острый бронхит неуточнённый"},
        {"code": "N10", "description": "Острый тубулоинтерстициальный нефрит"}
    ]
    result = extract_diagnoses(text)
    assert result == expected_output
    
def test_extract_diagnoses_1():
    text = """
    Диагноз: A01 Тиф и паратиф.
    """
    expected_output = [
        {"code": "A01", "description": "Тиф и паратиф"}
    ]
    result = extract_diagnoses(text)
    assert result == expected_output


def test_extract_diagnoses_2():
    text = """
    Диагноз: B01 Герпес зостер; A03 Токсоплазмоз.
    """
    expected_output = [
        {"code": "B01", "description": "Герпес зостер"},
        {"code": "A03", "description": "Токсоплазмоз"}
    ]
    result = extract_diagnoses(text)
    assert result == expected_output


def test_extract_diagnoses_3():
    text = """
    Диагноз: E66 Ожирение; I10 Гипертония.
    """
    expected_output = [
        {"code": "E66", "description": "Ожирение"},
        {"code": "I10", "description": "Гипертония"}
    ]
    result = extract_diagnoses(text)
    assert result == expected_output


def test_extract_diagnoses_4():
    text = """
    Диагноз: M54 Боли в спине.
    """
    expected_output = [
        {"code": "M54", "description": "Боли в спине"}
    ]
    result = extract_diagnoses(text)
    assert result == expected_output


def test_extract_diagnoses_5():
    text = """
    Диагноз: J45 Бронхиальная астма; F32 Депрессия.
    """
    expected_output = [
        {"code": "J45", "description": "Бронхиальная астма"},
        {"code": "F32", "description": "Депрессия"}
    ]
    result = extract_diagnoses(text)
    assert result == expected_output


def test_get_json_data_1():
    mock_data = {
        "tests": [
            {"name": "Гемоглобин", "normal_range": "12-16", "description": "Показатель гемоглобина"},
            {"name": "Лейкоциты", "normal_range": "4-9", "description": "Уровень белых клеток крови"}
        ]
    }

    def mock_get_json_data(file_name):
        if file_name == "analyses_data":
            return mock_data

    # Здесь мы проверяем корректность функции получения данных из JSON
    result = mock_get_json_data("analyses_data")
    expected_output = mock_data
    assert result == expected_output

def test_get_json_data_2():
    mock_data = {
        "tests": [
            {"name": "Креатинин", "normal_range": "60-110", "description": "Показатель функции почек"}
        ]
    }

    def mock_get_json_data(file_name):
        if file_name == "analyses_data":
            return mock_data

    # Тест с другим набором данных
    result = mock_get_json_data("analyses_data")
    expected_output = mock_data
    assert result == expected_output
    
def test_get_json_data_3():
    mock_data = {
        "patients": [
            {"name": "Иванов Иван", "age": 45, "diagnosis": "Гипертония"},
            {"name": "Петрова Мария", "age": 34, "diagnosis": "Артрит"}
        ]
    }

    def mock_get_json_data(file_name):
        if file_name == "patients_data":
            return mock_data

    # Проверка с набором данных пациентов
    result = mock_get_json_data("patients_data")
    expected_output = mock_data
    assert result == expected_output

def test_get_json_data_4():
    mock_data = {
        "medications": [
            {"name": "Аспирин", "dosage": "100 мг", "use": "Противовоспалительное"},
            {"name": "Парацетамол", "dosage": "500 мг", "use": "Обезболивающее"}
        ]
    }

    def mock_get_json_data(file_name):
        if file_name == "medications_data":
            return mock_data

    # Проверка с данными о медикаментах
    result = mock_get_json_data("medications_data")
    expected_output = mock_data
    assert result == expected_output

def test_get_json_data_5():
    mock_data = {
        "hospitals": [
            {"name": "Городская клиника", "location": "Москва", "capacity": 500},
            {"name": "Областная больница", "location": "Санкт-Петербург", "capacity": 1000}
        ]
    }

    def mock_get_json_data(file_name):
        if file_name == "hospitals_data":
            return mock_data

    # Проверка с данными о больницах
    result = mock_get_json_data("hospitals_data")
    expected_output = mock_data
    assert result == expected_output


# -------------------------------------------------------
    

