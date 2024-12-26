import requests
import json

from django.http import JsonResponse    

# Загружаем данные из JSON-файла
def load_disease_data(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_json_from_google_drive(file_id):
    """
    Загрузка JSON-файла из Google Диска по его ID.
    :param file_id: Идентификатор файла Google Drive.
    :return: Словарь с данными JSON.
    """
    # 1YbzJW_WSVW_evobKcBmwxtnyrb61hdL7
    base_url = f"https://drive.google.com/uc?id={file_id}&export=download"
    response = requests.get(base_url)
    if response.status_code == 200:
        try:
            return response.json()  # Возвращаем загруженные данные в формате JSON
        except json.JSONDecodeError:
            raise ValueError("Файл не содержит корректный JSON.")
    else:
        raise ConnectionError(f"Не удалось загрузить файл. Код ответа: {response.status_code}")
