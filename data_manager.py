from pymongo import MongoClient
from telegram_bot import logger

# Set up MongoDB connection
mongo_client = MongoClient(host="35.205.153.97")
db = mongo_client["my_data_base"]
collection = db["users"]


# insert new user into the db
def update_users(user_info):
    collection.insert_one(user_info)


def search_users_by_location(location):
    filter_location = {'location': location}
    projection = {"request": 1, 'phone': 1}
    result = collection.find(filter_location, projection)
    users = list([user for user in result])
    logger.info(f'Users that want help in location {location} > {[users]}')
    return users
