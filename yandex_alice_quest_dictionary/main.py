from flask import Flask
from flask import request
from yandex_alice_quest_dictionary.db.mongo import db_collection
import json, re
from dotenv import load_dotenv
from typing import Optional
from yandex_alice_quest_dictionary.db.mongo import Users, Dictionaries


load_dotenv("yandex_alice_quest_dictionary/.env")
app = Flask(__name__)
Users = db_collection("Users")


def get_all_dicts() -> list:
    out = []
    {
        "image_id": "<image_id>",
        "title": "Заголовок для изображения.",
        "description": "Описание изображения.",
        # "button": {
        #     "text": "Надпись на кнопке",
        #     "url": "https://example.com/",
        #     "payload": {}
        # }
    }
    for el in Dictionaries.get_all_rows({"status": "active"}):
        # el.pop('_id', None)
        out.append(
            {
                "image_id": el["img_id"],
                "title": el["name"],
                "description": el["description"],
            }
        )



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
    if len(Users.get_all_rows({"user" : user_id})) == 0:
        Users.add_row({"user" : user_id, "status" : "base"})
        dictionary_list = get_all_dicts()
        return "Привет, я бот организатор квеста!\n\
Спроси что я умею или сразу приступай к организации мероприятия.\n\
Доступные квесты:\n", dictionary_list
    else:
        dictionary_list = get_all_dicts()
        return "Привет рад снова тебя видеть, я бот организатор квеста!.\n\
Спроси что я умею или сразу приступай к организации мероприятия.\n\
Доступные квесты:", dictionary_list
#         return """Привет, я бот организатор квеста.
# Выбери подходящий квест. Для этого скажи его название.
# Доступные квесты:


# Ты так же можешь отредактировать квест под себя, для этого скажи "отредактировать квест".

# """

# ______________ Dicitionaries ___________________

# {
#     "name" : "name",
#     "desc" : "text",
#     "img_id" : "<img>",
#     "keys" : {
#       "key" : "value"
#     }
#     code: "test",
#     status: "active",
# }

# _________________________________________________


# ________________Users____________________________

# {
#     "user_id" : "<user_id>",
#     "state" : "<state>",
#     "keys" : {
#         "<dict_name>" : {
#             "key" : "value"
#         }
#     }
# }

# _________________________________________________


def handle_dialog(res,req):
    user_id = req["session"]["user_id"]
    if req['request']['original_utterance']:
        ## Проверяем, есть ли содержимое
        res['response']['text'] = req['request']['original_utterance']
    else:
        answ, buttons = hello(user_id)
        print(answ, buttons)
        res['response'] = {
            "card": {
                "type": "ItemsList",
                "header": {
                    "text": answ,
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
                # "footer": {
                #     "text": "Текст блока под изображением.",
                #     "button": {
                #         "text": "Надпись на кнопке",
                #         "url": "https://example.com/",
                #         "payload": {}
                #     }
                # }
            }
        }
        res['response']['buttons'] = buttons
        ## Если это первое сообщение — представляемся
        

def run():
    app.run()