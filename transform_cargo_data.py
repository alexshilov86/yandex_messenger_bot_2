# функция принимает массив объектов вида {"reciver_city": "Череповец", "all_cargos": [{"project": "13332", "project_cargos" : [{"art": "FRUX91105083 Дисплей Palmolive Jan23", "count": 1},{"art": "FRUX91105612 Навес Palmolive Июл24", "count": 1}]}]}
# и возвращает объект {"projects": [], "cargos": [{сумма по артикулам}]}

import json

def transform_cargo_string_data(json_string):
    # Заготовка для итогового результата
    result = {
        "projects": [],
        "cargos": [],
        "error": False
    }
    
    try:
        # Пытаемся распарсить строку
        data_list = json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        # Если строка сломана или пришел не строковый тип данных
        result["error"] = True
        return result

    # Если чтение прошло успешно, обрабатываем данные
    cargo_counts = {}
    
    for item in data_list:
        # Проверяем, что item является словарем (на случай некорректной структуры внутри массива)
        if not isinstance(item, dict):
            continue
            
        for cargo in item.get("all_cargos", []):
            if "project" in cargo:
                result["projects"].append(cargo["project"])
            
            for project_cargo in cargo.get("project_cargos", []):
                art = project_cargo.get("art")
                count = project_cargo.get("count", 0)
                if art:
                    cargo_counts[art] = cargo_counts.get(art, 0) + count
                    
    result["cargos"] = [{art: total_count} for art, total_count in cargo_counts.items()]
    
    return result
