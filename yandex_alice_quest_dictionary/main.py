from flask import Flask
from flask import request
from yandex_alice_quest_dictionary.db.mongo import db_collection
import json, re
from pprint import pformat
from dotenv import load_dotenv
import logging

from yandex_alice_quest_dictionary.db.mongo import Users, Dictionaries
from yandex_alice_quest_dictionary.handlers import hello, no_understanding, quest_state, base_state, settings, choose_quest

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

        with open("yandex_alice_quest_dictionary/all_text.json", "r",  encoding="utf-8") as file:
            read_json = json.load(file)
            self.alice_texts = read_json["texts"]
            self.alice_buttons = read_json["buttons"]

    def load(self, json_req: dict):
        self.response = {
            'session': json_req['session'],
            'version': json_req['version'],
            'response': {
                'end_session': False
            }
        }
        self.is_use_button = True
        self.is_start = False
        self.user_id = json_req["session"]["user_id"]
        self.dicts, self.dicts_descriptions = get_dicts_list_and_description()

        self.state = json_req["state"]["session"]

        self.input_text = json_req['request']['command'].strip().lower()
        
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
        
        if self.is_start:
            buttons = []
            buttons.append({
                "title" : "?????? ???? ?????????????"
            })
            self.response['response']['buttons'] = buttons  

        if self.is_use_button:
            buttons = []
            # for el in self.dicts:
            #     buttons.append({
            #         'title': el
            #     })

            if self.state["state"] == "quest":
                buttons.append({
                    "title" : "???????????????????? ??????????"
                })
            elif self.state["state"] == "choose_quest":
                buttons.append({"title" : "?????????????????? ??????????"})
                buttons.append({"title" : "?????????????????? ??????????"})
                buttons.append({"title" : "?????????????? ???????????? ??????????"})
            elif self.state["state"] == "settings":
                buttons.append({
                    "title" : "???????????????????? ??????????????????"
                })
            elif self.state["state"] == "start":
                pass
            else:
                buttons.append({"title" : "?????????????? ??????????"})
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
    ## ?????????????????? ?????????????????????? ????????????????????
    handle_dialog(Alice)
    return json.dumps(Alice.get_response())


def handle_dialog(Alice):
    if Alice.input_text == "" or Alice.input_text == "?????????????? ??????????":
        Alice.state = {
            "state" : "base"
        }
        Alice.is_use_button = False
        ## ??????????????????, ???????? ???? ????????????????????
        ## ???????? ?????? ???????????? ?????????????????? ??? ????????????????????????????
        answ, cards = hello(Alice)
        Alice.response['response'] = {
            "text" : answ,
            "card": {
                "type": "ItemsList",
                "header": {
                    "text": answ,
                },
                "items": cards
            }
        }
    elif Alice.state["state"] == "base":
        # logging.info(Alice.state)
        base_state(Alice)
    elif Alice.state["state"] == "choose_quest":
        # logging.info(Alice.state)
        choose_quest(Alice)
    elif Alice.state["state"] == "quest":
        # logging.info(Alice.state)
        quest_state(Alice)
    elif Alice.state["state"] == "settings":
        # logging.info(Alice.state)
        settings(Alice)
    else:
        # logging.info(Alice.state)
        Alice.state = {
            "state" : "base", 
        }
        no_understanding(Alice)

        
def run():
    app.run("0.0.0.0", port="5000")