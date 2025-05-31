import pandas as pd
import requests
import time
import os
from tkinter import Tk, filedialog

API_KEY = "3b8aa7fe-4a58-4c45-84f0-503ed957e939"
GEOCODER_URL = "https://geocode-maps.yandex.ru/1.x/"

Tk().withdraw()
file_path = filedialog.askopenfilename(
    title="Выберите файл с данными",
    filetypes=(
        ("Excel files", "*.xlsx"), 
        ("Excel 97-2003", "*.xls"),
        ("CSV files", "*.csv"),
        ("All files", "*.*")
    )
)

if not file_path:
    print("Файл не выбран, завершение программы.")
else:
    _, file_ext = os.path.splitext(file_path)
    file_ext = file_ext.lower()
    
    if file_ext == '.csv':
        data = pd.read_csv(file_path)
    elif file_ext in ('.xlsx', '.xls'):
        data = pd.read_excel(file_path, engine='openpyxl' if file_ext == '.xlsx' else 'xlrd')
    else:
        raise ValueError(f"Неподдерживаемый формат файла: {file_ext}")

    # Добавлена проверка колонки "Наименование"
    REQUIRED_COLUMNS = ["Город", "Наименование"]
    for col in REQUIRED_COLUMNS:
        if col not in data.columns:
            raise ValueError(f"Колонка '{col}' не найдена!")

    # Формируем поисковый запрос для организаций
    data["Поисковый запрос"] = data["Город"] + ", " + data["Наименование"]

    def get_organization_coordinates(query):
        params = {
            "apikey": API_KEY,
            "geocode": query,
            "format": "json",
            "kind": "org",  # Поиск именно организаций
            "results": 1    # Только первый результат
        }
        try:
            response = requests.get(GEOCODER_URL, params=params)
            response.raise_for_status()
            
            json_data = response.json()
            features = json_data["response"]["GeoObjectCollection"]["featureMember"]
            
            if not features:
                return {"longitude": 0, "latitude": 0}
                
            # Проверяем тип результата
            geo_object = features[0]["GeoObject"]
            if geo_object["metaDataProperty"]["GeocoderMetaData"]["kind"] != "org":
                return {"longitude": 0, "latitude": 0}
                
            coords = geo_object["Point"]["pos"].split()
            return {"longitude": float(coords[0]), "latitude": float(coords[1])}
            
        except Exception as e:
            print(f"Ошибка при обработке запроса '{query}': {str(e)}")
            return {"longitude": 0, "latitude": 0}

    coordinates = []
    total = len(data)
    for index, row in enumerate(data.iterrows(), 1):
        query = row[1]["Поисковый запрос"]
        result = get_organization_coordinates(query)
        coordinates.append(result)
        print(f"[{index}/{total}] Организация: {query} -> Координаты: {result}")
        time.sleep(0.2)  # Задержка для соблюдения лимитов API

    data["longitude"] = [coord["longitude"] for coord in coordinates]
    data["latitude"] = [coord["latitude"] for coord in coordinates]

    output_file = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=(
            ("Excel files", "*.xlsx"), 
            ("CSV files", "*.csv"),
            ("All files", "*.*")
        ),
        title="Сохранить результаты"
    )
    
    if output_file:
        if output_file.endswith('.csv'):
            data.to_csv(output_file, index=False)
        else:
            data.to_excel(output_file, index=False, engine='openpyxl')
        print(f"Файл сохранен: {output_file}")