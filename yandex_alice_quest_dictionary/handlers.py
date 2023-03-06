from yandex_alice_quest_dictionary.db.mongo import Users, Dictionaries
from random import choice
import logging


logging.basicConfig(level=logging.INFO)


def get_dicts_for_start() -> list:
    out = []
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


def hello(Alice):
    if len(Users.get_all_rows({"user_id" : Alice.user_id})) == 0:
        Users.new_user(Alice.user_id)
        dictionary_list = get_dicts_for_start()
        return Alice.alice_texts["hello_first"], dictionary_list
    else:
        dictionary_list = get_dicts_for_start()
        return Alice.alice_texts["hello_base"], dictionary_list


def quest_state(Alice):
    keys_dict = Alice.load_dict()
    key_word = Alice.input_text.lower()

    Alice.state["no_understanding"] = 0
    if key_word in ["остановить квест", "стоп"]:
        Alice.state["state"] = "choose_quest"
        Alice.response["response"]["text"] = Alice.alice_texts["quest_finish"]
    elif key_word not in keys_dict:
        Alice.response['response']['text'] = Alice.alice_texts["quest_wrong_key"]  
    else:
        Alice.response['response']['text'] = "%s: %s" % (choice(Alice.alice_texts["quest_good_key"]), keys_dict[key_word])


def base_state(Alice):
    if Alice.input_text.lower() == "выбрать квест":
        Alice.is_use_button = False
        Alice.is_start = True
        text = Alice.alice_texts["base_choose_quest"]
        Alice.response['response']['text'] = text
        _, cards = hello(Alice)
        Alice.response['response']["card"] = {
            "type": "ItemsList",
                "header": {
                    "text": text,
                },
                "items" : cards
        }  
        return
    elif Alice.input_text.lower() in Alice.dicts:
        Alice.response['response']['text'] = Alice.dicts_descriptions[Alice.input_text]
        Alice.state = {
            "state" : "choose_quest",
            "running_quest" : Alice.input_text,
        }
        Alice.state["no_understanding"] = 0
        return
    elif Alice.input_text.lower() == "что ты умеешь?":
        Alice.response['response']['text'] = Alice.alice_texts["description"]
        Alice.state["no_understanding"] = 0
        return
    no_understanding(Alice)


def choose_quest(Alice):
    if Alice.input_text.lower() == "запустить квест":
        Alice.response['response']['text'] = Alice.alice_texts["quest_start"]
        Alice.state["state"] = "quest"
        Alice.state["no_understanding"] = 0
        return
    elif Alice.input_text.lower() == "настроить квест":
        settings_choose_dict(Alice)
        Alice.state["state"] = "settings"
        Alice.state["no_understanding"] = 0
        return
    elif Alice.input_text.lower() == "выбрать другой квест":
        Alice.state["state"] = "base"
        Alice.is_use_button = False 
        text = Alice.alice_texts["choose_quest_after_finish"]
        Alice.response['response']['text'] = text
        _, cards = hello(Alice)
        Alice.response['response']["card"] = {
            "type": "ItemsList",
                "header": {
                    "text": text,
                },
                "items" : cards
        }  
        return
    no_understanding(Alice) 


def settings_choose_dict(Alice):
    key_word = Alice.state["running_quest"] 
    if key_word in Alice.dicts:
        Alice.response["response"]["text"] = Alice.alice_texts["setting_start"] % key_word
        Alice.state["status"] = "w8_key"
        return
    no_understanding(Alice)


def settings_get_key(Alice):
    keys_dict = Alice.load_dict()
    key_word = Alice.input_text.lower()
    if key_word not in keys_dict:
        Alice.response["response"]["text"] = Alice.alice_texts["setting_wrong_key"]
        return 
    Alice.state["status"] = "w8_value"
    Alice.state["choosen_key"] = key_word
    Alice.response["response"]["text"] = Alice.alice_texts["setting_good_key"] 


def settings_get_value(Alice):
    key_word = Alice.input_text.lower()
    
    user_dicts = Users.get_all_rows({"user_id" : Alice.user_id})[0]["keys"]
    if Alice.state["running_quest"] in user_dicts:
        temp_dict = user_dicts[Alice.state["running_quest"]]
    else:
        temp_dict = {}
    temp_dict[Alice.state["choosen_key"]] = key_word
    user_dicts[Alice.state["running_quest"]] = temp_dict
    Users.change_data({"user_id": Alice.user_id}, {"keys" : user_dicts})
    
    Alice.response["response"]["text"] = Alice.alice_texts["setting_setup"] % (
        Alice.state["running_quest"],
        Alice.state["choosen_key"],
        key_word,
    )
    Alice.state["status"] = "w8_key"


def settings(Alice):
    key_word = Alice.input_text.lower()
    
    if key_word in ["остановить настройку", "стоп"]:
        Alice.state["state"] = "choose_quest"
        Alice.response["response"]["text"] = Alice.alice_texts["setting_end"]
    
    elif Alice.state["status"] == "choose_dict":
        settings_choose_dict(Alice)

    elif Alice.state["status"] == "w8_key":
        settings_get_key(Alice)

    elif Alice.state["status"] == "w8_value":
        settings_get_value(Alice)


def no_understanding(Alice):  
    if Alice.state["no_understanding"] >= 3:
        Alice.state["state"] = "base"
        Alice.response['response']['text'] = Alice.alice_texts["no_understate_more"]
        _, cards = hello(Alice)
        Alice.response['response']["card"] = {
            "type": "ItemsList",
            "header": {
                "text": Alice.alice_texts["no_understate_more"],
            },
            "items" : cards
        }
        return
    Alice.response['response']['text'] = Alice.alice_texts["no_understate"]
    Alice.state["no_understanding"] += 1