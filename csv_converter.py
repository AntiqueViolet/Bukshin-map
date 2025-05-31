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

    REQUIRED_COLUMNS = ["Город", "Адрес"]
    for col in REQUIRED_COLUMNS:
        if col not in data.columns:
            raise ValueError(f"Колонка '{col}' не найдена!")

    data["Полный адрес"] = data["Город"] + ", " + data["Адрес"]

    def get_coordinates(address):
        params = {
            "apikey": API_KEY,
            "geocode": address,
            "format": "json",
        }
        response = requests.get(GEOCODER_URL, params=params)
        if response.status_code == 200:
            try:
                geo_object = response.json()["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
                coords = geo_object["Point"]["pos"].split(" ")
                return {"longitude": float(coords[0]), "latitude": float(coords[1])}
            except (IndexError, KeyError):
                return {"longitude": None, "latitude": None}
        else:
            return {"longitude": None, "latitude": None}

    coordinates = []
    for index, row in data.iterrows():
        address = row["Полный адрес"]
        result = get_coordinates(address)
        coordinates.append(result)
        print(f"Обработан адрес: {address} -> {result}")
        time.sleep(0.2)  

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