from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId

client = MongoClient("mongodb://127.0.0.1:27017")
db = client.cv_matcher
collection = db.offers

def save_offer_and_cvs(offer_text, selected_cvs, title):
    doc = {
        "title": title,
        "offer_text": offer_text,
        "selected_cvs": selected_cvs,
        "date_saved": datetime.now().isoformat()
    }
    collection.insert_one(doc)

def load_saved_offers():
    return list(collection.find())

def delete_offer(offer_id):
    collection.delete_one({"_id": ObjectId(offer_id)})

def delete_cv_from_offer(offer_id, cv_name):
    collection.update_one(
        {"_id": ObjectId(offer_id)},
        {"$pull": {"selected_cvs": {"cv_name": cv_name}}}
    )
