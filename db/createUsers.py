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

def hash_passwords(password):
  salt = bcrypt.gensalt()
  hashed = bcrypt.hashpw(password.encode('utf-8'), salt)

  return hashed.decode('utf-8')


if __name__ == "__main__":

  load_dotenv()

  name = ["Admin"]
  username = ["admin"]
  passwords = ["admin123"]

  hashed_passwords = [hash_passwords(password) for password in passwords]

  mongo_user = st.secrets['MONGO_USER']
  mongo_pass = st.secrets["MONGO_PASS"]

  username_mongo = urllib.parse.quote_plus(mongo_user)
  password_mongo = urllib.parse.quote_plus(mongo_pass)

  client = MongoClient("mongodb+srv://%s:%s@cluster0.gjkin5a.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0" % (username_mongo, password_mongo))
  db = client.estoquecmdr
  coll = db.Usuarios

  new_user = {
    "name": name,
    "username": username,
    "password":hashed_passwords[0]
  }

  result = coll.insert_one(new_user)

  print(f"Documentos inseridos com os IDs: {result.inserted_id}")