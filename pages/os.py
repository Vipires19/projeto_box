import streamlit as st
import pandas as pd
import plotly.express as px
import pickle
import streamlit_authenticator as stauth
from pathlib import Path
import datetime
import os
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import urllib
import urllib.parse
import certifi
from db.getUsersInfo import login as db_login
from db.insertSale import register_sale

from datetime import datetime, timedelta, timezone
import pytz

mongo_user = st.secrets['MONGO_USER']
mongo_pass = st.secrets["MONGO_PASS"]

username = urllib.parse.quote_plus(mongo_user)
password = urllib.parse.quote_plus(mongo_pass)

ca = certifi.where()
client = MongoClient("mongodb+srv://%s:%s@cluster0.gjkin5a.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0" % (username, password), tlsCAFile=ca)
st.cache_resource = client
db = client.estoquecmdr
coll = db.estoque
coll2 = db.Vendas
coll3 = db.pagamentos
coll4 = db.clientes
coll5 = db.Usuarios
coll6 = db.mecanicos
coll7 = db.servicos

st.set_page_config(
            layout =  'wide',
            page_title = 'Ordens de Serviço',
        )


# --- Authentication ---
# Load hashed passwords
file_path = Path('comodoro.py').parent/"db"/"hashed_pw.pkl"

with file_path.open("rb") as file:
  hashed_passwords = pickle.load(file)

user = coll5.find({})
users = []
for item in user:
    item.pop('_id', None)
    users.append(item)

usuarios = {'usernames' : {}}
for item in users:
    usuarios['usernames'][item['username']] = {'name' : item['name'], 'password' : item['password'][0]}
  
credentials = usuarios

authenticator = stauth.Authenticate(credentials= credentials, cookie_name= 'random_cookie_name', cookie_key='key123', cookie_expiry_days= 1)
authenticator.login()

fuso_horario_brasilia = pytz.timezone("America/Sao_Paulo")

if 'vendas' not in st.session_state:
	st.session_state['vendas'] = []

def increment_counter(venda):
	st.session_state['vendas'].append(venda)

def decrement_counter(venda):
	st.session_state['vendas'].remove(venda)
     
def vendas():
    df = st.session_state['estoque_1']
               
    st.markdown('**Estoque**')
    st.dataframe(df)
    
    st.divider()

    col1,col2,col3,col4,col5,col6,col7 = st.columns(7)
    produto = df['Produto'].value_counts().index
    produtos = col1.selectbox('Produto', produto)
    quantidade = col2.number_input('Quantidade', min_value=0)
    valor_un = col3.number_input('Valor Unitário', min_value=0)
    valor_total =  valor_un * quantidade
    valor = col4.metric('Valor de total', f'R$ {valor_total :,.2f}')

    venda = {'Produto' : produtos,
             'Quantidade' : quantidade,
             'Valor' : valor_total}

    add = col5.button('Adicionar produto')
    if add:
        increment_counter(venda)
    
    vendas = st.session_state['vendas']

    delete = col5.button('Remover produto')
    if delete:
        decrement_counter(venda)

    clear = col5.button('Limpar venda')
    if clear:
        st.session_state['vendas'] = []

    st.markdown('Cadastro de novos mecânicos')
    nome_cliente = st.text_input('Nome mecanico:')
    col1,col2 = st.columns(2)
    cadastrar = col1.button('Cadastrar')
    if cadastrar:
        coll6.insert_many([{'nome' : nome_cliente}])
    deletar = col2.button('Excluir')
    if deletar:
        coll6.delete_one({'nome' : nome_cliente})
    
    st.divider()

    df_venda = pd.DataFrame(vendas, columns = ['Produto', 'Quantidade', 'Valor'])
    col1,col2,col3,col4,col5,col6,col7 = st.columns(7)
    col1.dataframe(df_venda)

    cadastro = coll4.find({})
    clientesdf = []
    for item in cadastro:
        clientesdf.append(item)

    clientesdf = pd.DataFrame(clientesdf, columns= ['_id', 'nome'])
    clientesdf.drop(columns='_id', inplace=True)

    meca = coll6.find({})
    mecanicodf = []
    for item in meca:
        mecanicodf.append(item)

    mecanicodf = pd.DataFrame(mecanicodf, columns= ['_id', 'nome'])
    mecanicodf.drop(columns='_id', inplace=True)

    servico_total = int(df_venda['Valor'].sum())
    valor_servico = col2.metric('Valor do serviço', f'R$ {servico_total :,.2f}')
    nome = clientesdf['nome'].value_counts().index
    cliente = col3.selectbox('Nome do cliente', nome)
    mecanic = mecanicodf['nome'].value_counts().index
    mecanico = col4.selectbox('Nome do mecânico', mecanic)
    pagamento = ['Pix', 'Cartão de crédito', 'Dinheiro', 'Desconto em folha']
    forma_pagamento = col5.selectbox('Forma de pagamento', pagamento)
    data_debito = col6.date_input('Data do débito', format='DD.MM.YYYY')

    if forma_pagamento == 'Desconto em folha':
            quantidade_semanas = col7.number_input('Quantidade de semana', min_value= 0)
            sell = {'Código' : 4,
                    'Venda' : vendas,
                    'Valor' : servico_total,
                    'Cliente' : cliente,
                    'Mecanico' : mecanico,
                    'Data do débito' : str(data_debito),
                    'Forma de pagamento' : forma_pagamento,
                    'Quantidade de semanas' : quantidade_semanas}
    
    else: 
        sell = {'Código' : 4,
                'Venda' : vendas,
                'Valor' : servico_total,
                'Cliente' : cliente,
                'Mecanico' : mecanico,
                'Data do débito' : str(data_debito),
                'Forma de pagamento' : forma_pagamento}

    confirma = st.button('Confirmar serviço')
    if confirma:
        tempo_agora = datetime.now(fuso_horario_brasilia)
        data_utc = tempo_agora
        if isinstance(data_utc, datetime):
            data_brasilia = data_utc.astimezone(fuso_horario_brasilia)
            tempo_agora = data_brasilia.strftime('%d/%m/%Y %H:%M') 
        sell.update({'Data da venda' : tempo_agora})
        entry = [sell]
        coll7.insert_many(entry)
        coll2.insert_many(entry)
        
        for produto in vendas:
           product = produto['Produto']
           finalsell = produto['Quantidade'] 
           coll.update_one({'Produto': product}, {'$set' : {'Quantidade' : int(df[df['Produto'] == product]['Quantidade'].values - finalsell)}})
        
        st.session_state['vendas'] = []
        st.rerun()

def pagina_principal():
    col1,col2 = st.columns(2)
    col1.title('**BOX Comodoro**')
    col2.image('files/WhatsApp Image 2025-01-04 at 11.51.06.jpeg', width=200)
    st.markdown('Ordens de serviço referentes a manutenção das motos!')

    btn = authenticator.logout()
    if btn:
        st.session_state["authentication_status"] == None

    st.divider()

    vendas()
            
def main():
    if st.session_state["authentication_status"]:
    
        pagina_principal()
  
    elif st.session_state["authentication_status"] == False:
        st.error("Username/password is incorrect.")

    elif st.session_state["authentication_status"] == None:
        st.warning("Please insert username and password")

if __name__ == '__main__':

    main()