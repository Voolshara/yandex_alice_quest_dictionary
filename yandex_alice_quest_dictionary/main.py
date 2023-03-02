from flask import Flask
from flask import request
from yandex_alice_quest_dictionary.db.mongo import db_collection
import json, re
from pprint import pformat
from random import choice
from dotenv import load_dotenv
import logging

from yandex_alice_quest_dictionary.db.mongo import Users, Dictionaries
from yandex_alice_quest_dictionary.handlers import hello, no_understanding



def get_dicts_list_and_description():
    just_list = []
    desc = {}
    for el in Dictionaries.get_all_rows({"status": "active"}):
        just_list.append(el["name"])
        desc[el["name"]] = el["description"]
    return just_list, desc


class Alice_Worker:
    def __init__(self) -> None:
        self.state = {}
        self.buttons = []
        self.cards = []
        self.text = ""

    def load(self, json_req: dict):
        self.response = {
            'session': json_req['session'],
            'version': json_req['version'],
            'response': {
                'end_session': False
            }
        }
        self.user_id = json_req["session"]["user_id"]
        self.dicts, self.dicts_descriptions = get_dicts_list_and_description()

        self.state = json_req["state"]["session"]

        self.input_text = json_req['request']['command']
        
    def load_dict(self):
        now_quest = self.state["running_quest"]
        keys = Dictionaries.get_all_rows({
            "status" : "active",
            "name" : now_quest
        })[0]["keys"]


        custom_keys = Users.get_all_rows({
            "user_id" : self. user_id  
        })[0]["keys"]

        if now_quest in custom_keys:
            for el in custom_keys[now_quest]:
                keys[el] = custom_keys[now_quest][el]

        return keys

    def set_quest_status(self):
        state_data = dict()
        state_data["running_quest"] = self.input_text
        state_data["state"] = "quest"
        self.state = state_data


    def get_response(self):
        self.response["session_state"] = self.state
        buttons = []
        # for el in self.dicts:
        #     buttons.append({
        #         'title': el
        #     })

        if self.state["state"] == "quest":
            buttons.append({
                "title" : "Оставновить квест"
            })
        elif self.state["state"] == "start":
            pass
        else:
            buttons.append({"title" : "Выбрать квест"})
            buttons.append({"title" : "Настроить квест"})
        self.response['response']['buttons'] = buttons  
        
        # logging.info(pformat(self.response))
        return self.response
    

load_dotenv("yandex_alice_quest_dictionary/.env")
logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
Alice = Alice_Worker()


@app.route('/yandex_skill', methods=['POST'])
def main():
    Alice.load(request.json)
    ## Заполняем необходимую информацию
    handle_dialog(Alice)
    return json.dumps(Alice.get_response())


def on_quest_state(Alice):
    keys_dict = Alice.load_dict()
    key_word = Alice.input_text

    if key_word not in keys_dict:
        Alice.response['response']['text'] = "Неправильное ключевое слово\nПопробуй ещё раз"
    
    elif key_word.lower() in ["оставновить квест", "стоп"]:
        Alice.state = {
            "state" : "base"
        }
        Alice.response["response"]["text"] = "Спасибо за игру. Квест остановлен"
    else:
        keys = ["Локация", "Искомое место", "Здесь", "Посмотри тут"]
        Alice.response['response']['text'] = "%s: %s" % (choice(keys), keys_dict[key_word])


def prepare_quest(Alice):
    print(Alice.input_text in Alice.dicts)
    if Alice.input_text in Alice.dicts:
        Alice.response['response']['text'] = Alice.dicts_descriptions[Alice.input_text]
        Alice.set_quest_status()
        return
    elif Alice.input_text.lower == "что ты умеешь":
        Alice.response['response']['text'] = "Привет, я проведу для тебя квест. Выбери один из доступных. Ты так же можешь настроить ключевые слова под себя"
        return
    no_understanding(Alice)


def handle_dialog(Alice):
    if Alice.input_text == "" or Alice.input_text == "Выбрать квест":
        Alice.state = {
                "state" : "base"
            }
        ## Проверяем, есть ли содержимое
        ## Если это первое сообщение — представляемся
        answ, buttons = hello(Alice)
        Alice.response['response'] = {
            "text" : answ,
            "card": {
                "type": "ItemsList",
                "header": {
                    "text": answ,
                },
                "items": buttons
            }
        }
    elif Alice.state["state"] == "base":
        prepare_quest(Alice)
    elif Alice.state["state"] == "quest":
        on_quest_state(Alice)
    else:
        no_understanding(Alice)

        
def run():
    app.run("0.0.0.0", port="5000")