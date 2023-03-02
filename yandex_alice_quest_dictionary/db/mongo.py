import os, re, logging, json
from typing import Optional

from pprint import pformat
from typer import Typer

from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv(".env")
logging.basicConfig(level=logging.INFO)

CONNECTION_STRING = "mongodb://{}:{}@{}/".format(
    os.getenv("MONGO_USER"),
    os.getenv("MONGO_PASSWORD"),
    os.getenv("MONGO_HOST"),
    # os.getenv("MONGO_PORT"),
)
# set db
db = MongoClient(CONNECTION_STRING).athome


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


class MongoDatabase():
    def __init__(self):
        pass

    def add_row(self, row: dict) -> None:
        db[self.collection_name].insert_one(row)

    def get_list_of_collections(self) -> list:
        return db.list_collection_names()
    
    def find_by_sort(self, by_sort: list):
        return db[self.collection_name].find_one(sort=by_sort)
    
    def get_all_rows(self, row):
        out = []
        for x in db[self.collection_name].find(row):
            x.pop("_id", None)
            out.append(x)
        return out
    
    def get_all_unique(self, row):
        return [x for x in db[self.collection_name].distinct("keys", row)]
    
    def drop_collection(self):
        db[self.collection_name].drop()

    def change_data(self, query: dict, update: dict):
        new_update = {"$set" : update}
        db[self.collection_name].update_one(query, new_update)

class db_collection(MongoDatabase):
    def __init__(self, name_of_collection):
        self.collection_name = name_of_collection


class Users_class(MongoDatabase):
    def __init__(self):
        self.collection_name = "Users"

    def new_user(self, user_id) -> None:
        self.add_row({
            "user_id": user_id,
            "state" : "base", 
            "keys" : {}
        })

    def change_dict(self, user_id, diict_name):
        pass

    def get_user_dicts(self, user_id):
        pass


class Dictionaries_class(MongoDatabase):
    def __init__(self):
        self.collection_name = "Dictionaries"
    
    def new_dict(self, code: str, name: str, description: str, img_id: str, keys: dict) -> None:
        self.add_row({
            "code" : code, 
            "name": name,
            "description": description,
            "img_id": img_id,
            "keys": keys,
            "status" : "active",
        })
    
    def get_dict_data(self, name: str) -> Optional[dict]:
        return self.get_all_unique({
            "name": name
        })

    # def get_value_of_dict(self, name: str, key) -> Optional[str]:
    #     return self.get_all_unique({
    #         "name" : name,
    #         "keys" : {

    #         }
    #     })

Users = Users_class()
Dictionaries = Dictionaries_class()

def check_file(path, file: str, extension: str, type_of_opening) -> bool:
    path_file = os.path.join(path, file + extension)
    if os.path.isfile(path_file):
        return True
    return False
    

def get_file_data(path, file: str, extension: str, type_of_opening) -> Optional[str]:
    path_file = os.path.join(path, file + extension)
    out = None
    if type_of_opening == "rb":
        if os.path.isfile(path_file):
            with open(path_file, type_of_opening) as f:
                out = f.read()
    else:
        if os.path.isfile(path_file):
            with open(path_file, type_of_opening, encoding='utf-8') as f:
                out = f.read()
    return out


def setup_dicitionaries():    
    path =  "/".join(str(__file__).split("/")[:-3]) + "/dictionaries"
    for f in os.listdir(path):
        if not re.match(r'.*\.csv', f):
            continue
        
        dict_name = f[:-4]
        csv_data = get_file_data(path, dict_name, ".csv", "r")
        if csv_data is None:
            continue
        
        desc_data = get_file_data(path, dict_name, ".txt", "r")
        if desc_data is None:
            desc_data = "Тестовый квест\nОчень хороший квест"
        
        img_extension = [".png", ".jpg", ".jpeg"]
        img_exe_index = 0
        while not check_file(path, dict_name, img_extension[img_exe_index], "rb"):
            img_exe_index += 1 
            if img_exe_index >= len(img_extension):
                break
        if img_exe_index == 3:
            img = "quest.png"
        else:
            img = dict_name + img_extension[img_exe_index]

        stream = os.popen("curl \
-H 'Authorization: OAuth %s' \
-H 'Content-Type: multipart/form-data' \
-X POST \
-F file=@%s \
'https://dialogs.yandex.net/api/v1/skills/%s/images'" % (
            os.getenv("oauth_token"),
            os.path.join(path, img),
            os.getenv("alice_token"),
))
        output = stream.read()
        photo_id = json.loads(output)["image"]["id"]   

        # photo_id = "888"

        collection = {}
        for line in csv_data.split("\n")[1:]:
            if line == "":
                continue
            key, value = map(lambda x: x.strip(), line.split(", "))
            collection[key.lower()] = value.lower()

        Dictionaries.new_dict(
            dict_name.strip().lower(),
            desc_data.split("\n")[0].lower(), 
            "\n" .join(desc_data.split("\n")[1:]),
            photo_id, 
            collection,
            )

        logging.info(f"[ADD DICT] {dict_name}\n%s "% desc_data.split("\n")[0] + pformat(collection))


drop_dictionaries = Typer()
@drop_dictionaries.command()
def run_drop(*, code: str):
    if code ==  "*":
        Dictionaries.drop_collection()
    elif code == "users":
        Users.drop_collection()    
    else:
        Dictionaries.change_data(
            {"code": code.strip(), "status": "active"},
            {"status": "deactive"}
        )
    get_data()

    
get_data = Typer()
@get_data.command()
def run_get_data(*, db: str) -> None:
    if db == "users":
        out = Users.get_all_rows({})
        for el in out:
            el.pop('_id', None)
        logging.info(pformat(out))
    else:
        out = Dictionaries.get_all_rows({"status": "active"})
        for el in out:
            el.pop('_id', None)
        logging.info(pformat(out))