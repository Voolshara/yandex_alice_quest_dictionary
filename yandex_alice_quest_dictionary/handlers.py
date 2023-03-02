from yandex_alice_quest_dictionary.db.mongo import Users, Dictionaries


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
    if len(Users.get_all_rows({"user" : Alice.user_id})) == 0:
        Users.add_row({"user" : Alice.user_id, "status" : "base"})
        dictionary_list = get_dicts_for_start()
        return "Привет, я бот организатор квеста!\n\
Спроси что я умею или сразу приступай к квесту.\n\
Доступные квесты:\n", dictionary_list
    else:
        dictionary_list = get_dicts_for_start()
        return "Привет, я бот организатор квеста. Рад тебя видеть.\nСпроси что я умею или сразу приступай к квесту.\nДоступные квесты:", dictionary_list


def no_understanding(Alice):
    Alice.state = {
        "state" : "base", 
    }
    Alice.response['response']['text'] = "Я тебя не понял. Выбери квест или настрой его под себя"