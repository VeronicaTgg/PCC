from flask_login import UserMixin
from pyairtable.formulas import match
from .db import get_db

class User(UserMixin):
    def __init__(self, id_, name, email, profile_pic, locale):
        self.id = id_
        self.name = name
        self.email = email
        self.profile_pic = profile_pic
        self.locale = locale

    @staticmethod
    def get(user_id):
        db = get_db()
        formula = match({"google_id": "{}".format(user_id)})
        user = db.first("Users", formula=formula) 
        # if not exists return None
        if not user:
            return None
        # if exists return a new instance of user
        new_user = User(
            id_=user["fields"]["google_id"], name=user["fields"]["name"], email=user["fields"]["email"], profile_pic=user["fields"]["profile_pic"], locale=user["fields"]["locale"]
        )
        # return a new instance of user
        return new_user
    
    # create a new user on the db
    @staticmethod
    def create(id_, name, email, profile_pic, locale):
        db = get_db()
        db.create("Users", {
            "google_id": id_,
            "name": name,
            "email": email,
            "profile_pic": profile_pic,
            "locale": locale
        })

        

        
        
