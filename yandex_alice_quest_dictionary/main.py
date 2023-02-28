from flask import Flask
from flask import request
from yandex_alice_quest_dictionary.db.mongo import db_collection
import json, re
from pprint import pp
from dotenv import load_dotenv
from typing import Optional
from yandex_alice_quest_dictionary.db.mongo import Users, Dictionaries


load_dotenv("yandex_alice_quest_dictionary/.env")
app = Flask(__name__)
Users = db_collection("Users")


def get_dicts_list_and_description(user_id: str):
    just_list = []
    desc = {}
    for el in Dictionaries.get_all_rows({"status": "active"}):
        just_list.append(el["name"])
        desc[el["name"]] = el["description"]
    return just_list
        

def get_all_dicts() -> list:
    out = []
    # {
    #     "image_id": "<image_id>",
    #     "title": "Заголовок для изображения.",
    #     "description": "Описание изображения.",
    #     # "button": {
    #     #     "text": "Надпись на кнопке",
    #     #     "url": "https://example.com/",
    #     #     "payload": {}
    #     # }
    # }
    for el in Dictionaries.get_all_rows({"status": "active"}):
        out.append(
            {
                "image_id": el["img_id"],
                "title": el["name"],
                "description": el["description"],
                "button": {
                    "text": el["name"],
                }
            }
        )
    return out


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
Спроси что я умею или сразу приступай к квесту.\n\
Доступные квесты:\n", dictionary_list
    else:
        dictionary_list = get_all_dicts()
        return "Привет рад снова тебя видеть, я бот организатор квеста!.\nСпроси что я умею.\nДоступные квесты:", dictionary_list




def handle_dialog(res,req):
    user_id = req["session"]["user_id"]
    dict_list, dict_desc = get_dicts_list_and_description(user_id)
    if req['request']['original_utterance'] == "":
        ## Проверяем, есть ли содержимое
        ## Если это первое сообщение — представляемся
        answ, buttons = hello(user_id)
        res['response'] = {
            "text" : answ,
            "card": {
                "type": "ItemsList",
                "header": {
                    "text": answ,
                },
                "items": buttons
                # [
                #     {
                #         "image_id": "<image_id>",
                #         "title": "Заголовок для изображения.",
                #         "description": "Описание изображения.",
                #         "button": {
                #             "text": "Надпись на кнопке",
                #             "url": "https://example.com/",
                #             "payload": {}
                #         }
                #     }
                # ],
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
    elif req['request']['original_utterance'] in dict_list:
        res['response']['text'] = dict_desc[req['request']['original_utterance']]       


def run():
    app.run("0.0.0.0", port="5000")