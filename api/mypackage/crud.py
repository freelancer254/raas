from . import schemas
from typing import List
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user(db, user_key: str):
    return db.get(user_key)

def get_user_by_username(db, username: str):
    return db.fetch({"email?contains": "@","username": username.lower()}).items

def get_user_by_email(db, email: str):
    return db.fetch({"email": email.lower()}).items

async def create_user(db, user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user: dict = { 
    "username": user.username.lower(),
    "email": user.email.lower(),
    "hashed_password": hashed_password,
    "is_active": True 
    }
    db.put(db_user)
    return {"data": "Your Account Has Been Successfully Created!"}

def get_latest_draws(db):
    return db.fetch({"numWords?gt": 0}).items

#return all the draws for a particular user
def get_user_draws(db, username: str):
    fetched_draws =  db.fetch({"numWords?gt": 0,"username": username.lower()})
    all_draws = fetched_draws.items
    while fetched_draws.last:
        fetched_draws =  db.fetch({"numWords?gt": 0,"username": username.lower()}, last=fetched_draws.last)
        all_draws += fetched_draws.items
    return all_draws

def get_draw(db, requestId: str ):
    return db.fetch({"numWords?gt":0, "requestId":requestId}).items

def get_draw_unfulfilled(db, requestId: str):
    return db.fetch({"numWords":0, "requestId":requestId}).items

def update_draw(db,request, draw):
    updates = {
        "numWords":len(request[5]),
        "randomWords":str(request[5])
    }
    key = draw[0].get('key')
    db.update(updates, key)


def create_user_draw(db, draw: dict):
    db_draw = db.put(draw)
    return db_draw
