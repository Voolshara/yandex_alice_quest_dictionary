import datetime
import os
from contextlib import contextmanager
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func

from dotenv import load_dotenv


load_dotenv("yandex_alice_quest_dictionary/.env")
engine = sa.create_engine(
    'postgresql://{}:{}@{}:{}/{}'.format(
        os.getenv('PG_NAME'),
        os.getenv('PG_PASSWORD'),
        os.getenv('PG_HOST'),
        os.getenv('PG_PORT'),
        os.getenv('PG_DB_NAME'),
    )
)
Session = sessionmaker(bind=engine)
Base = declarative_base()


@contextmanager
def create_session(**kwargs):
    new_session = Session(**kwargs)
    try:
        yield new_session
        new_session.commit()
    except Exception:
        new_session.rollback()
        raise
    finally:
        new_session.close()


class User(Base):
    __tablename__ = 'User'
    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.String())
    state = sa.Column(sa.String(), default="base")


class Dicitonaries(Base):
    __tablename__ = 'Dicitonaries'
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String())
    user_bind = sa.Column(sa.INTEGER, sa.ForeignKey(User.id))
    status = sa.Column(sa.Boolean(), default=True)


class Keys(Base):
    __tablename__ = 'Keys'
    id = sa.Column(sa.Integer, primary_key=True)
    key = sa.Column(sa.String())
    value = sa.Column(sa.String())
    dictionary_bind = sa.Column(sa.INTEGER(), sa.ForeignKey(Dicitonaries.id))


def get_user_id(user_id: str) -> int:
    with create_session() as session:
        user_response = session.query(User).filter(User.user_id == user_id).one_or_none()
        if user_response is None:
            return -1
        return user_response.id
    

def get_dict_id(name: str, user_bind: str) -> int:
    with create_session() as session:
        dict_response = session.query(Dicitonaries).filter(sa.and_(Dicitonaries.name == name, Dicitonaries.user_bind == user_bind)).one_or_none()
        if dict_response is None:
            return -1
        return dict_response.id
    

def get_all_dicts(user_bind: str) -> list:
    with create_session() as session:
        dict_response = session.query(Dicitonaries).filter(sa.or_(Dicitonaries.user_bind == user_bind, Dicitonaries.user_bind == 1)).all()
        return [x.name for x in dict_response]


def new_user(user_id: str) -> int:
    with create_session() as session:
        session.add(
            User(user_id = user_id)
    )
    id = get_user_id(user_id)
    if id == -1:
        return new_user(user_id)
    return id


def new_dictionary(name: str, user_bind: str) -> int:
    with create_session() as session:
        session.add(Dicitonaries(name=name, user_bind=user_bind))
    dict_id = get_dict_id(name, user_bind)
    if dict_id == -1:
        return new_dictionary(name, user_bind)
    return dict_id


def new_key(key: str, value: str, dictionary_bind: str):
    with create_session() as session:
        qu = session.add(Keys(key=key, value=value, dictionary_bind=dictionary_bind))


def create_all_tables():
    Base.metadata.create_all(engine)


def setup_base_data():
    create_all_tables()
    user_base = new_user("base")
    dict_space = new_dictionary("space", user_base)
    new_key("Альтаир", "Холодильник", dict_space)
    new_key("Регул", "Подоконник", dict_space)
    new_key("Алия", "Кровать", dict_space)
    print("[DONE]")
    
