# функция ищет накладную в базе и возвращает форматированый ответ для отправки
import json
import os
from transform_cargo_data import transform_cargo_string_data

def find_nakl_from_base(nakl):
    local_data_file = os.getenv("LOCAL_DATA_FILE", "base_data.json")

    # считываем файл в data
    try:
        with open(local_data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        print("Данные успешно загружены")
    except FileNotFoundError:
        print(f"Файл {local_data_file} не найден")
        data = {}
        return {"error": True, "msg" : "Ошибка доступа к базе"}
    except json.JSONDecodeError as e:
        print(f"Ошибка формата JSON: {e}")
        data = {}
        return {"error": True, "msg" : "Ошибка доступа к базе"}
    
    # поиск в базе

    NAKL_COLUMN_INDEX_MAP = {
        "Отгружено": 20,   # column1
        "Готовится к отгрузке": 20,      # column2
        "Контрольный диапазон": 20,
        "Заявки": 20
    }

    nakl_clean = str(nakl).strip()
    for sheet_name, sheet_data in data.items():
        rows = sheet_data["rows"]
        col_index = NAKL_COLUMN_INDEX_MAP.get(sheet_name)
        if col_index is None:
            continue

        for row_idx, row in enumerate(rows):
            if col_index < len(row) and str(row[col_index]).strip() == nakl_clean:
                return {
                    "error": False,
                    "msg": "Накладная найдена",
                    "_source_sheet": sheet_name,
                    "_row_index": row_idx,
                    "values": row
                }
        return {"error": True, "msg": "Накладная не найдена"}

def msg_by_nakl(nakl):
    # функция формирует текстовую строку для накладной
    result = find_nakl_from_base(nakl)
    if (result["error"]):
        return result["msg"]
    
    otpr_json = "[" + result["values"][38] + "]"
    transformed_date = transform_cargo_string_data(otpr_json)
    msg = "Город назначения: " + result["values"][8] + '\n' + "Получатель: " + result["values"][10]+ '\n'

    msg = msg + "Проекты " + " - ".join(transformed_date["projects"]) + '\n'
    msg = msg + "Материалы "+ '\n' + "\n".join(f"{k} - {v} шт" for item in transformed_date["cargos"] for k, v in item.items())

    return msg

print (msg_by_nakl("26-03681066599"))