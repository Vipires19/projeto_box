import pickle
from pathlib import Path
import bcrypt
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import urllib
import urllib.parse
import os
from dotenv import load_dotenv
import streamlit as st

import streamlit_authenticator as stauth


load_dotenv()

mongo_user = st.secrets['MONGO_USER']
mongo_pass = st.secrets["MONGO_PASS"]

username = urllib.parse.quote_plus(mongo_user)
password = urllib.parse.quote_plus(mongo_pass)

client = MongoClient("mongodb+srv://%s:%s@cluster0.gjkin5a.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0" % (username, password))
db = client.estoquecmdr
coll = db.Usuarios


def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def info_to_login(user, password):

    filter = {
        "username": user
    }

    query_result = coll.find_one(filter)

    hashed_pass = query_result['password']

    control_login = check_password(password, hashed_pass)

    if control_login :

        return True
    
    else:
        return False




def login(user, password):

    control = info_to_login(user, password)

    return control