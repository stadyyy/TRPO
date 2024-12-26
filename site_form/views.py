from django.shortcuts import render
from django.http import HttpResponse
from .models import MedicalDocument
from .text_utils import extract_text_from_pdf, extract_tables_from_pdf, extract_diagnoses_and_analyses, find_potential_status, get_json_data, collect_diseases_status  # Функция извлечения текста

def upload_and_analyze(request):
    if request.method == 'POST' and request.FILES.get('medical-document'):
        uploaded_file = request.FILES['medical-document']
        
        # Проверяем формат файла
        if uploaded_file.content_type != 'application/pdf':
            return HttpResponse("Ошибка: можно загружать только PDF-файлы.")
        
        # Сохраняем документ
        doc = MedicalDocument(file=uploaded_file)
        doc.save()
        
        # Извлекаем текст из PDF
        extract_tables_from_pdf(uploaded_file)
        text = extract_text_from_pdf(uploaded_file)
        
        diagnoses, analisis = extract_diagnoses_and_analyses(text)
        diseases = collect_diseases_status(diagnoses)
        
        return render(request, "show_diseases.html", {"diseases": diseases, "analyses": analisis})
    
    return render(request, 'index.html')
