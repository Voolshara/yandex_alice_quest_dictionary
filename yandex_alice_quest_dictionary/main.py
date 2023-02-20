from flask import Flask
from flask import request
from yandex_alice_quest_dictionary.db.db import get_user_id, new_user, get_all_dicts
import json
from dotenv import load_dotenv


load_dotenv("yandex_alice_quest_dictionary/.env")

app = Flask(__name__)

@app.route('/yandex_skill', methods=['POST'])
def main():
    ## Создаем ответ
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    ## Заполняем необходимую информацию
    handle_dialog(response, request.json)
    return json.dumps(response)


def hello(user_id: int):
    user_db_id = get_user_id(user_id)
    if user_db_id == -1:
        user_db_id = new_user(user_id)
        dictionary_list = get_all_dicts(user_db_id)
        return "Привет, я бот организатор квеста!\n\
Спроси что я умею или сразу приступай к организации мероприятия.\n\
Доступные квесты:\n\n" + "\n".join(dictionary_list), dictionary_list + ['Настройка квестов']
    else:
        dictionary_list = get_all_dicts(user_db_id)
        return "Привет рад снова тебя видеть, я бот организатор квеста!.\n\
Спроси что я умею или сразу приступай к организации мероприятия.\n\
Доступные квесты:\n\n" + "\n".join(dictionary_list), dictionary_list + ['Настройка квестов']
#         return """Привет, я бот организатор квеста.
# Выбери подходящий квест. Для этого скажи его название.
# Доступные квесты:


# Ты так же можешь отредактировать квест под себя, для этого скажи "отредактировать квест".

# """




def handle_dialog(res,req):
    user_id = req["session"]["user_id"]
    if req['request']['original_utterance']:
        ## Проверяем, есть ли содержимое
        res['response']['text'] = req['request']['original_utterance']
    else:
        answ, buttons = hello(user_id)
        
        res['response'] = {
            "card": {
                "type": "ItemsList",
                "header": {
                    "text": "Заголовок списка изображений",
                },
                "items": [
                    {
                        "image_id": "<image_id>",
                        "title": "Заголовок для изображения.",
                        "description": "Описание изображения.",
                        "button": {
                            "text": "Надпись на кнопке",
                            "url": "https://example.com/",
                            "payload": {}
                        }
                    }
                ],
                "footer": {
                    "text": "Текст блока под изображением.",
                    "button": {
                        "text": "Надпись на кнопке",
                        "url": "https://example.com/",
                        "payload": {}
                    }
                }
            }
        }
        res['response']['buttons'] = buttons
        ## Если это первое сообщение — представляемся
        

def run():
    app.run()