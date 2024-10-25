from pymongo import MongoClient
from pymongo.server_api import ServerApi
import urllib
import urllib.parse
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import pytz
import streamlit as st

def register_sale(name_func, quantity_func, sale_func, cliente, forma_pagamento, data_debito):

    def check_quantity(name, quantity):
        doc = coll_estoque.find_one({'Nome': name})

        doc_description = doc.get('Descrição', 0)
        doc_code = doc.get('Código', 0)

        if doc:
            quantidade_atual = doc.get('Quantidade', 0)

            if quantidade_atual - quantity < 0:
                return False
        
            return True, doc_description, doc_code


    try:
        load_dotenv()
        mongo_user = st.secrets['MONGO_USER']
        mongo_pass = st.secrets["MONGO_PASS"]

        username = urllib.parse.quote_plus(mongo_user)
        password = urllib.parse.quote_plus(mongo_pass)

        client = MongoClient("mongodb+srv://%s:%s@cluster0.gjkin5a.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0" % (username, password))

        db = client.estoquecmdr
        coll_vendas = db.Vendas
        coll_estoque = db.estoque

        query_filter = {'Nome' : name_func}

        control_venda, desc_venda, code_venda = check_quantity(name_func, quantity_func)


        fuso_horario_brasilia = pytz.timezone("America/Sao_Paulo")

        # Obter a data e hora atuais no horário de Brasília
        tempo_agora = datetime.now(fuso_horario_brasilia)

        if control_venda:
            att = {"$inc": {"Quantidade": -quantity_func}}
            resultado = coll_estoque.update_one(query_filter, att)

            # Adicionar a venda na tabela de vendas
            venda = coll_vendas.insert_one({'Nome': name_func, 'Código': code_venda, 'Quantidade': quantity_func, 
                                            'Descrição': desc_venda, 'Valor de venda': sale_func, 'Data da venda': tempo_agora, 'Cliente' : cliente, 'Forma de pagamento' : forma_pagamento, 'Data Débito': data_debito})

            print(f"Produto atualizado com sucesso e com ID {resultado}")

            return "Sucesso" , True
        
        else:

            return "Venda deixará o estoque negativo", False

    except Exception as ex:

        print (ex.args)

        return ex.args , False
    
    finally:
        client.close()

def register_sale_desc(name_func, quantity_func, sale_func, cliente, forma_pagamento, data_debito, quant_semana):

    def check_quantity(name, quantity):
        doc = coll_estoque.find_one({'Nome': name})

        doc_description = doc.get('Descrição', 0)
        doc_code = doc.get('Código', 0)

        if doc:
            quantidade_atual = doc.get('Quantidade', 0)

            if quantidade_atual - quantity < 0:
                return False
        
            return True, doc_description, doc_code


    try:
        load_dotenv()
        mongo_user = st.secrets['MONGO_USER']
        mongo_pass = st.secrets["MONGO_PASS"]

        username = urllib.parse.quote_plus(mongo_user)
        password = urllib.parse.quote_plus(mongo_pass)

        client = MongoClient("mongodb+srv://%s:%s@cluster0.gjkin5a.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0" % (username, password))

        db = client.estoquecmdr
        coll_vendas = db.Vendas
        coll_estoque = db.estoque

        query_filter = {'Nome' : name_func}

        control_venda, desc_venda, code_venda = check_quantity(name_func, quantity_func)


        fuso_horario_brasilia = pytz.timezone("America/Sao_Paulo")

        # Obter a data e hora atuais no horário de Brasília
        tempo_agora = datetime.now(fuso_horario_brasilia)

        if control_venda:
            att = {"$inc": {"Quantidade": -quantity_func}}
            resultado = coll_estoque.update_one(query_filter, att)

            # Adicionar a venda na tabela de vendas
            venda = coll_vendas.insert_one({'Nome': name_func, 'Código': code_venda, 'Quantidade': quantity_func, 
                                            'Descrição': desc_venda, 'Valor de venda': sale_func, 'Data da venda': tempo_agora, 'Cliente' : cliente, 'Forma de pagamento' : forma_pagamento, 'Data Débito': data_debito, 
                                            'Quantidade semanas' : quant_semana})

            print(f"Produto atualizado com sucesso e com ID {resultado}")

            return "Sucesso" , True
        
        else:

            return "Venda deixará o estoque negativo", False

    except Exception as ex:

        print (ex.args)

        return ex.args , False
    
    finally:
        client.close()
