from datetime import datetime, timedelta

from bson.objectid import ObjectId
from fastapi import FastAPI, HTTPException, Depends
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["members"]
collection = db["users"]


# Define a Pydantic model for the User schema
class User(BaseModel):
    name: str
    email: str
    password: str


# Define a Pydantic model for the Login schema
class Login(BaseModel):
    email: str
    password: str


# Define a Pydantic model for the JWT Token schema
class Token(BaseModel):
    access_token: str
    token_type: str


# Define password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create a FastAPI app
app = FastAPI()


# Create a route to create a new user
@app.post("/users")
def create_user(user: User):
    # Check if the email already exists
    if collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    # Hash the password
    hashed_password = pwd_context.hash(user.password)
    # Insert the new user into MongoDB
    user_dict = user.dict()
    user_dict["password"] = hashed_password
    result = collection.insert_one(user_dict)
    # Return the newly created user
    new_user = collection.find_one({"_id": result.inserted_id})
    new_user["_id"] = str(new_user["_id"])
    return new_user


# Helper function to generate a JWT access token
def create_access_token(subject: str, expires_delta: timedelta = timedelta(minutes=15)):
    to_encode = {"sub": subject, "exp": datetime.utcnow() + expires_delta}
    encoded_jwt = jwt.encode(to_encode, "secret_key", algorithm="HS256")
    return encoded_jwt


# Helper function to get the JWT token from the Authorization header
async def get_token(authorization: str = Depends()):
    if not authorization:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    parts = authorization.split()
    if parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    elif len(parts) == 1:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    elif len(parts) > 2:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = parts[1]
    return token


# Helper function to get the current user from the JWT token
async def get_current_user(token: str = Depends(get_token)):
    try:
        payload = jwt.decode(token, "secret_key", algorithms=["HS256"])
        user = collection.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="Invalid user ID")
        user["_id"] = str(user["_id"])
        return User(**user)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# Create a route to get a user by ID
@app.get("/users/{user_id}")
def read_user(user_id: str, current_user: User = Depends(get_current_user)):
    # Check if the ID is valid
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")
    # Get the user from MongoDB
    user = collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user["_id"] = str(user["_id"])
    return user


# Create a route to authenticate a user and return a JWT token
@app.post("/login")
def login(login: Login):
    # Check if the email exists
    user = collection.find_one({"email": login.email})
    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or password")
    # Check if the password is correct
    if not pwd_context.verify(login.password, user["password"]):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    # Generate a JWT token
    access_token = create_access_token(str(user["_id"]))
    token = Token(access_token=access_token, token_type="bearer")
    return token
