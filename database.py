from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["ai_allergy_db"]

users = db["users"]
history = db["history"]


def save_history(data):
    history.insert_one(data)


def get_history(username):
    return history.find({"username": username}).sort("_id", -1)
