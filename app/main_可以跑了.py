from json import JSONEncoder

from bson import ObjectId
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)


app = FastAPI()
app.json_encoder = CustomJSONEncoder

client = MongoClient("mongodb://mongodb:27017/")
db = client["mydatabase"]
users_collection = db["users"]


class User(BaseModel):
    username: str
    password: str


@app.post("/users/")
async def create_user(user: User):
    print('001')
    if users_collection.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already taken")
    print('002')
    user_dict = user.dict()
    print('003')
    users_collection.insert_one(user_dict)
    print('004')
    del user_dict["password"]
    print('005')
    return 'hi'


@app.post("/login/")
async def login_user(user: User):
    stored_user = users_collection.find_one({"username": user.username, "password": user.password})
    if not stored_user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"message": "Logged in successfully"}
