import json
import csv
import chardet
import copy

def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        rawdata = f.read(10000) 
    return chardet.detect(rawdata)['encoding']

def main():
    with open('open.json', 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)
    
    csv_encoding = detect_encoding('baza2gis.csv')
    print(f"Определена кодировка CSV файла: {csv_encoding}")
    
    # Создаем словарь для пространственной индексации (сетка с шагом 0.0001)
    dgis_grid = {}
    
    # Загружаем данные из CSV
    with open('baza2gis.csv', 'r', encoding=csv_encoding) as csvfile:
        dialect = csv.Sniffer().sniff(csvfile.read(1024))
        csvfile.seek(0)
        
        reader = csv.reader(csvfile, dialect)
        headers = next(reader)
        
        # Ищем столбцы с координатами
        lon_col = None
        lat_col = None
        possible_lon_names = ['K', 'longitude', 'долгота', 'lon', 'x']
        possible_lat_names = ['L', 'latitude', 'широта', 'lat', 'y']
        
        for i, header in enumerate(headers):
            header_clean = header.strip().lower()
            if header_clean in [name.lower() for name in possible_lon_names]:
                lon_col = i
            if header_clean in [name.lower() for name in possible_lat_names]:
                lat_col = i
        
        if lon_col is None or lat_col is None:
            raise ValueError("Не удалось найти столбцы с координатами")
        
        print(f"Используются столбцы: долгота={headers[lon_col]}, широта={headers[lat_col]}")
        
        # Заполняем пространственный индекс
        for row in reader:
            try:
                lon = float(row[lon_col].replace(',', '.'))
                lat = float(row[lat_col].replace(',', '.'))
                
                # Ключ сетки (округление до 4 знаков = шаг 0.0001)
                grid_key = (round(lon * 10000), round(lat * 10000))
                
                if grid_key not in dgis_grid:
                    dgis_grid[grid_key] = []
                dgis_grid[grid_key].append((lon, lat))
            except (ValueError, TypeError, IndexError) as e:
                print(f"Ошибка обработки строки: {row}. Ошибка: {e}")
                continue

    # Списки для результатов
    new_features = []
    orange_copies = []
    epsilon = 0.0005  # Погрешность сравнения
    
    # Помечаем точки в GeoJSON
    for feature in geojson_data['features']:
        g_lon, g_lat = feature['geometry']['coordinates']
        base_key = (round(g_lon * 10000), round(g_lat * 10000))
        
        # Определяем диапазон ячеек для поиска (±0.0005)
        search_range = 5  # 0.0005 / 0.0001 = 5
        found = False
        
        # Проверяем все ячейки в диапазоне ±5 шагов (соответствует ±0.0005)
        for dx in range(-search_range, search_range + 1):
            for dy in range(-search_range, search_range + 1):
                neighbor_key = (base_key[0] + dx, base_key[1] + dy)
                if neighbor_key in dgis_grid:
                    for d_lon, d_lat in dgis_grid[neighbor_key]:
                        # Точная проверка с погрешностью epsilon
                        if abs(d_lon - g_lon) <= epsilon and abs(d_lat - g_lat) <= epsilon:
                            found = True
                            break
                    if found:
                        break
            if found:
                break
        
        if found:
            # Создаем оранжевую копию
            copy_feature = copy.deepcopy(feature)
            if 'options' in copy_feature and isinstance(copy_feature['options'], dict):
                copy_feature['options']['preset'] = 'islands#orangeIcon'
            else:
                copy_feature['options'] = {'preset': 'islands#orangeIcon'}
            orange_copies.append(copy_feature)
        
        # Оригинальная точка
        new_features.append(feature)
    
    # Добавляем оранжевые копии в конец
    new_features.extend(orange_copies)
    geojson_data['features'] = new_features

    # Сохраняем результат
    with open('open_with_2gis.json', 'w', encoding='utf-8') as f:
        json.dump(geojson_data, f, ensure_ascii=False, indent=2)
    
    print("Обработка завершена. Результат сохранен в open_with_2gis.json")

if __name__ == '__main__':
    main()