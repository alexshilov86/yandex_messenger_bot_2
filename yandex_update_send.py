import requests

url = "http://127.0.0.1:8000/webhook"
update = {
    "updates": [
        {
            "update_id": "123456789",
            "message": {
                "id": "msg_1",
                "text": "Привет, бот!",
                "from": {
                    "id": "user_123",
                    "display_name": "Иван Иванов",
                    "login": "ivan.ivanov@organization.ru"
                },
                "chat": {
                    "id": "chat_abc",
                    "type": "private"
                }
            }
        }

    ]
}




response = requests.post(url, json=update)
print(response.json())