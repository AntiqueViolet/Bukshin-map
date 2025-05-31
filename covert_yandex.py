import json
import chardet
import copy
import pandas as pd  # Добавлено для работы с Excel

def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        rawdata = f.read(10000) 
    return chardet.detect(rawdata)['encoding']

def main():
    with open('open_with_2gis.json', 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)
    
    # Чтение данных из Excel
    try:
        df = pd.read_excel('bazayandex.xlsx', engine='openpyxl')
        print("Файл XLSX успешно прочитан")
        
        # Проверка наличия необходимых столбцов
        if 'X' not in df.columns or 'Y' not in df.columns:
            raise ValueError("В файле отсутствуют столбцы X и/или Y")
            
        # Преобразование в список координат
        dgis_points = []
        for _, row in df.iterrows():
            try:
                lon = float(row['X'])
                lat = float(row['Y'])
                dgis_points.append((lon, lat))
            except (ValueError, TypeError):
                continue
                
        print(f"Загружено {len(dgis_points)} координат из XLSX")
        
    except Exception as e:
        print(f"Ошибка при чтении XLSX: {e}")
        return

    # Создаем словарь для пространственной индексации
    dgis_grid = {}
    for lon, lat in dgis_points:
        grid_key = (round(lon * 10000), round(lat * 10000))
        if grid_key not in dgis_grid:
            dgis_grid[grid_key] = []
        dgis_grid[grid_key].append((lon, lat))

    # Списки для результатов
    new_features = []
    orange_copies = []
    epsilon = 0.0005  # Погрешность сравнения
    
    # Помечаем точки в GeoJSON
    for feature in geojson_data['features']:
        g_lon, g_lat = feature['geometry']['coordinates']
        base_key = (round(g_lon * 10000), round(g_lat * 10000))
        
        search_range = 5
        found = False
        
        for dx in range(-search_range, search_range + 1):
            for dy in range(-search_range, search_range + 1):
                neighbor_key = (base_key[0] + dx, base_key[1] + dy)
                if neighbor_key in dgis_grid:
                    for d_lon, d_lat in dgis_grid[neighbor_key]:
                        if abs(d_lon - g_lon) <= epsilon and abs(d_lat - g_lat) <= epsilon:
                            found = True
                            break
                    if found:
                        break
            if found:
                break
        
        if found:
            copy_feature = copy.deepcopy(feature)
            copy_feature.setdefault('options', {})['preset'] = 'islands#yellowIcon'
            orange_copies.append(copy_feature)
        
        new_features.append(feature)
    
    new_features.extend(orange_copies)
    geojson_data['features'] = new_features

    with open('open_with_2gis_yandex.json', 'w', encoding='utf-8') as f:
        json.dump(geojson_data, f, ensure_ascii=False, indent=2)
    
    print("Обработка завершена. Результат сохранен в open_with_2gis_yandex.json")

if __name__ == '__main__':
    main()