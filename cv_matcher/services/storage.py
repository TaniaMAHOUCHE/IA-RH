from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
from config import MONGO_URI, DB_NAME
import numpy as np

class MongoDB:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[DB_NAME]

    def add_annonce(self, titre, service, desc_fr, desc_en, skills):
        if self.db.annonces.find_one({"titre": titre}):
            return None  

        doc = {
            "titre": titre,
            "service": service,
            "description_fr": desc_fr,
            "description_en": desc_en,
            "skills": skills,
            "date_creation": datetime.now(),
            "cvs": []
        }
        return self.db.annonces.insert_one(doc).inserted_id

    def get_annonces(self):
        return list(self.db.annonces.find())

    def delete_annonce(self, annonce_id):
        oid = ObjectId(annonce_id) if not isinstance(annonce_id, ObjectId) else annonce_id
        self.db.cvs.delete_many({"annonce_id": oid})
        self.db.annonces.delete_one({"_id": oid})

    def add_cv(self, annonce_id, filename, cv_fr, cv_en, infos, score, auto):
        oid = ObjectId(annonce_id) if not isinstance(annonce_id, ObjectId) else annonce_id

        if self.db.cvs.find_one({"annonce_id": oid, "filename": filename}):
            return None  

        if isinstance(auto, (np.bool_, np.bool)):
            auto = bool(auto)

        doc = {
            "annonce_id": oid,
            "filename": filename,
            "cv_fr": cv_fr,
            "cv_en": cv_en,
            "infos_extraites": infos,
            "score": score,
            "auto_enregistre": auto,
            "date_upload": datetime.now()
        }
        cv_id = self.db.cvs.insert_one(doc).inserted_id
        self.db.annonces.update_one({"_id": oid}, {"$push": {"cvs": cv_id}})
        return cv_id

    def get_cvs_by_annonce(self, annonce_id):
        oid = ObjectId(annonce_id) if not isinstance(annonce_id, ObjectId) else annonce_id
        return list(self.db.cvs.find({"annonce_id": oid}))

    def delete_cv(self, cv_id):
        oid = ObjectId(cv_id) if not isinstance(cv_id, ObjectId) else cv_id
        cv = self.db.cvs.find_one({"_id": oid})
        if cv:
            self.db.annonces.update_one(
                {"_id": cv["annonce_id"]}, {"$pull": {"cvs": oid}}
            )
            self.db.cvs.delete_one({"_id": oid})

    def count_cvs(self):
        return self.db.cvs.count_documents({})
