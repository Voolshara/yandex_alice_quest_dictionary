from yandex_alice_quest_dictionary.db.mongo import Users, Dictionaries
from random import choice


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
        return "Привет, я бот организатор квеста!\n\
Спроси что я умею или сразу приступай к квесту.\n\
Доступные квесты:\n", dictionary_list
    else:
        dictionary_list = get_dicts_for_start()
        return "Привет, я бот организатор квеста. Рад тебя видеть.\nСпроси что я умею или сразу приступай к квесту.\nДоступные квесты:", dictionary_list


def quest_state(Alice):
    keys_dict = Alice.load_dict()
    key_word = Alice.input_text.lower()

    Alice.state["no_understanding"] = 0
    if key_word in ["остановить квест", "стоп"]:
        Alice.state = {
            "state" : "base"
        }
        Alice.response["response"]["text"] = "Спасибо за игру. Квест остановлен"
    elif key_word not in keys_dict:
        Alice.response['response']['text'] = "Неправильное ключевое слово\nПопробуй ещё раз"
    
    else:
        keys = ["Локация", "Искомое место", "Здесь", "Посмотри тут"]
        Alice.response['response']['text'] = "%s: %s" % (choice(keys), keys_dict[key_word])


def base_state(Alice):
    if Alice.input_text.lower() == "выбрать квест":
        text = "Давай начнём. Выбери квест"
        Alice.response['response']['text'] = text
        _, cards = hello(Alice)
        Alice.response['response']["card"] = {
            "type": "ItemsList",
                "header": {
                    "text": text,
                },
                "items" : cards
        }  
    elif Alice.input_text.lower() in Alice.dicts:
        Alice.response['response']['text'] = Alice.dicts_descriptions[Alice.input_text]
        Alice.state = {
            "state" : "choose_quest",
            "running_quest" : Alice.input_text,
        }
        Alice.state["no_understanding"] = 0
        return
    elif Alice.input_text.lower() == "что ты умеешь":
        Alice.response['response']['text'] = "Привет, я проведу для тебя квест. Выбери один из доступных. Ты так же можешь настроить ключевые слова под себя"
        Alice.state["no_understanding"] = 0
        return
    no_understanding(Alice)


def choose_quest(Alice):
    if Alice.input_text.lower() == "запустить квест":
        Alice.response['response']['text'] = "Начинаем квест. Скажи ключевое слово. А я тебе подскажу место."
        Alice.state["state"] = "quest"
        Alice.state["no_understanding"] = 0
    elif Alice.input_text.lower() == "настроить квест":
        settings_choose_dict(Alice)
        Alice.state["state"] = "settings"
        Alice.state["no_understanding"] = 0
    no_understanding(Alice) 


def settings_choose_dict(Alice):
    key_word = Alice.state["running_quest"] 
    if key_word in Alice.dicts:
        Alice.response["response"]["text"] = "Приступаем к изменнию ключевых слов: %s. Скажи ключевое слово, а после новое значение" % key_word
        Alice.state["status"] = "w8_key"
        return
    no_understanding(Alice)


def settings_get_key(Alice):
    keys_dict = Alice.load_dict()
    key_word = Alice.input_text.lower()
    if key_word not in keys_dict:
        Alice.response["response"]["text"] = "Неправильное ключевое слово\nПопробуй ещё раз"       
        return 
    Alice.state["status"] = "w8_value"
    Alice.state["choosen_key"] = key_word
    Alice.response["response"]["text"] = "Какое место будет?"       


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
    
    Alice.response["response"]["text"] = "Для события: %s изменено ключевое слово %s на %s\nСкажите следущее ключевое слово" % (
        Alice.state["running_quest"],
        Alice.state["choosen_key"],
        key_word,
    )
    Alice.state["status"] = "w8_key"


def settings(Alice):
    key_word = Alice.input_text.lower()
    
    if key_word in ["остановить настройку", "стоп"]:
        Alice.state = {
            "state" : "base"
        }
        Alice.response["response"]["text"] = "Готово. Изменения внесены."
    
    elif Alice.state["status"] == "choose_dict":
        settings_choose_dict(Alice)

    elif Alice.state["status"] == "w8_key":
        settings_get_key(Alice)

    elif Alice.state["status"] == "w8_value":
        settings_get_value(Alice)

    


    # elif key_word not in keys_dict:
    #     Alice.response['response']['text'] = "Неправильное ключевое слово\nПопробуй ещё раз"
    # else:
    #     keys = ["Локация", "Искомое место", "Здесь", "Посмотри тут"]
    #     Alice.response['response']['text'] = "%s: %s" % (choice(keys), keys_dict[key_word])

    # Alice.response['response']['text'] = "QU"


def no_understanding(Alice):  
    if Alice.state["no_understanding"] == 3:
        Alice.response['response']['text'] = "Я запутался. Давай начнём сначала.\nВебри квест"
        _, cards = hello(Alice)
        Alice.response['response']["card"] = {
            "type": "ItemsList",
            "header": {
                "text": "Я запутался. Давай начнём сначала.\nВебри квест",
            },
            "items" : cards
        }
        return
    Alice.response['response']['text'] = "Я тебя не понял. Попробуй повторить"
    Alice.state["no_understanding"] += 1