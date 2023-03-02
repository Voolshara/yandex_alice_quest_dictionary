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

    if key_word not in keys_dict:
        Alice.response['response']['text'] = "Неправильное ключевое слово\nПопробуй ещё раз"
    
    elif key_word in ["оставновить квест", "стоп"]:
        Alice.state = {
            "state" : "base"
        }
        Alice.response["response"]["text"] = "Спасибо за игру. Квест остановлен"
    else:
        keys = ["Локация", "Искомое место", "Здесь", "Посмотри тут"]
        Alice.response['response']['text'] = "%s: %s" % (choice(keys), keys_dict[key_word])


def base_state(Alice):
    if Alice.input_text in Alice.dicts:
        Alice.response['response']['text'] = Alice.dicts_descriptions[Alice.input_text]
        Alice.set_quest_status()
        return
    
    elif Alice.input_text.lower() == "что ты умеешь":
        Alice.response['response']['text'] = "Привет, я проведу для тебя квест. Выбери один из доступных. Ты так же можешь настроить ключевые слова под себя"
        return
    
    elif Alice.input_text.lower() == "настроить квест":
        text = "Здесь ты можешь изменить ключевые слова. Выбери квест, который хочешь изменить:"
        Alice.response['response']['text'] = text
        _, cards = hello(Alice)
        Alice.resonse['response']["card"] = {
            "type": "ItemsList",
                "header": {
                    "text": text,
                },
                "items" : cards
        }
        
        Alice.state = {
            "state" : "settings"
        }
        
        return

    no_understanding(Alice)


def settings(Alice):
    Alice.response['response']['text'] = "QU"


def no_understanding(Alice):
    Alice.state = {
        "state" : "base", 
    }
    Alice.response['response']['text'] = "Я тебя не понял. Выбери квест или настрой его под себя"