from django.apps import AppConfig
from .utils import load_json_from_google_drive
from django.conf import settings

class SiteFormConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'site_form'

    def ready(self):
        # Загружаем JSON при запуске приложения
        diseases_file_id = settings.GOOGLE_DRIVE_DISEASES_JSON_FILE_ID
        try:
            self.disease_data = load_json_from_google_drive(diseases_file_id)
            print("JSON успешно загружен из Google Диска.")
        except Exception as e:
            print(f"Ошибка при загрузке JSON: {e}")

        
        analysis_file_id = settings.GOOGLE_DRIVE_ANALYSES_JSON_FILE_ID
        try:
            self.analyses_data = load_json_from_google_drive(analysis_file_id)
            print("JSON успешно загружен из Google Диска.")
        except Exception as e:
            print(f"Ошибка при загрузке JSON: {e}")
