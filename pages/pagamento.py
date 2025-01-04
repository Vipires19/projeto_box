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
            page_title = 'Pagamento',
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

def pesquisa_pgto():
    df = st.session_state['hist_full']
    fuso_horario_brasilia = pytz.timezone("America/Sao_Paulo")
    cliente = df['Cliente'].value_counts().index
    clientes = st.selectbox('Motoca', cliente)
    df_motoca = df[df['Cliente'] == clientes]
    df_motoca_1 = df_motoca[df_motoca['Código'] == 1][['Data da venda', 'Produto' ,'Quantidade', 'Valor da venda', 'Forma de pagamento', 'Data do débito', 'Quantidade de semanas']]
    df_motoca_2 = df_motoca[df_motoca['Código'] == 2][['Data da venda', 'Data do vale', 'Valor da venda', 'Forma de pagamento', 'Data do débito', 'Quantidade de semanas']]
    df_motoca_3 = df_motoca[df_motoca['Código'] == 3][['Data da venda', 'Produto' , 'Moto', 'Data do aluguel', 'Quantidade de dias', 'Valor do aluguel', 'Forma de pagamento', 'Data do débito', 'Quantidade de semanas']]
    df_motoca_4 = df_motoca[df_motoca['Código'] == 4][['Data da venda', 'Valor', 'Forma de pagamento', 'Data do débito', 'Quantidade de semanas', '_id','Venda', 'Mecanico']]
    
    
    col1,col2 = st.columns(2)
    col1.header('Produtos')
    col1.dataframe(df_motoca_1)
    col2.header('Vale/Antecipação')
    col2.dataframe(df_motoca_2)
    col1.header('Aluguel Moto')
    col1.dataframe(df_motoca_3)
    col2.header('Ordens de serviço')
    col2.dataframe(df_motoca_4[['Data da venda', 'Valor', 'Forma de pagamento', 'Data do débito', 'Quantidade de semanas', '_id']])

    categoria = df['Código'].value_counts().index
    cat = st.selectbox('Cod', categoria)
    if cat == 1:
        #nome = hist_1['Cliente'].value_counts().index
        #cliente = st.selectbox('Cliente', nome)
        #df_cliente = hist_1[hist_1['Cliente'] == cliente]
        #df_cliente
        prod = df_motoca_1['Produto'].value_counts().index
        produto = st.selectbox('Prod.', prod)
        df_produto = df_motoca_1[df_motoca_1['Produto'] == produto]
        
    
        col1,col2,col3,col4 = st.columns(4)

        datetime_obj = datetime.strptime(df_produto['Data da venda'].value_counts().index[0], '%d/%m/%Y %H:%M')
        data1 = str(datetime_obj).split(' ')[0].split('-')[0]
        data2 = str(datetime_obj).split(' ')[0].split('-')[1]
        data3 = str(datetime_obj).split(' ')[0].split('-')[2]
        data_metric = f'{data3}/{data2}/{data1}'

        quantidade = df_produto['Quantidade'].value_counts().index
        valor = df_produto['Valor da venda'].value_counts().index[0]
        forma_pgto = df_produto['Forma de pagamento'].value_counts().index[0]

        data_debit = df_produto['Data do débito'].value_counts().index[0]
        data_d1 = str(data_debit).split(' ')[0].split('-')[0]
        data_d2 = str(data_debit).split(' ')[0].split('-')[1]
        data_d3 = str(data_debit).split(' ')[0].split('-')[2]
        data_d = f'{data_d3}/{data_d2}/{data_d1}'
    
        col1.metric('Data da venda', data_metric)
        col2.metric('Produto', produto )
        col3.metric('Quantidade', quantidade)
        col4.metric('Valor', f'R$ {valor:,.2f}')
        col1.metric('Forma de pagamento', forma_pgto)
        col2.metric('Data do débito', data_d)

        if forma_pgto == 'Desconto em folha':
            quantidade_semanas = df_produto['Quantidade de semanas'].value_counts().index[0]
    
            if quantidade_semanas != 0:
                val_pal = valor/quantidade_semanas
                col3.metric('Quantidade de semanas', quantidade_semanas)
                col4.metric('Valor da parcela', f'R${val_pal:,.2f}')
                pagamento = {'Cliente' : clientes,
                             'Produto' : produto,
                             'Valor' : val_pal,
                            'Forma pagamento' : forma_pgto}
            
        else:
            pagamento = {'Cliente' : clientes,
                         'Produto' : produto,
                         'Valor' : valor,
                         'Forma pagamento' : forma_pgto}            

        baixa_no_pagamento = col1.button('Confirmar pagamento')
        if baixa_no_pagamento:
            tempo_agora = datetime.now(fuso_horario_brasilia)
            data_utc = tempo_agora
            if isinstance(data_utc, datetime):
                data_brasilia = data_utc.astimezone(fuso_horario_brasilia)
                tempo_agora = data_brasilia.strftime('%d/%m/%Y')
            pagamento.update({'Data do pagamento' : tempo_agora})
            coll3.insert_many([pagamento])
        
        log_atendimento = coll3.find({'Produto' : produto, 'Cliente' : clientes})

        log_atendimentodf = []
        for item in log_atendimento:
               log_atendimentodf.append(item)

        container = st.container(border=True)
        with container:
            if log_atendimentodf == []:
                pass
            else:
                pd.DataFrame(log_atendimentodf)[['Data do pagamento','Forma pagamento', 'Valor']]

    if cat == 2:
        #hist_2 = st.session_state['hist_2']
        #nome = hist_2['Cliente'].value_counts().index
        #cliente = st.selectbox('Cliente', nome)
        #df_cliente = hist_2[hist_2['Cliente'] == cliente]
        #df_cliente
        prod = df_motoca_2['Data da venda'].value_counts().index
        produto = st.selectbox('Vale', prod)
        df_produto = df_motoca_2[df_motoca_2['Data da venda'] == produto]
    
        col1,col2,col3,col4 = st.columns(4)

        datetime_obj = datetime.strptime(df_produto['Data da venda'].value_counts().index[0], '%d/%m/%Y %H:%M')
        data1 = str(datetime_obj).split(' ')[0].split('-')[0]
        data2 = str(datetime_obj).split(' ')[0].split('-')[1]
        data3 = str(datetime_obj).split(' ')[0].split('-')[2]
        data_metric = f'{data3}/{data2}/{data1}'

        quantidade = df_produto['Quantidade'].value_counts().index
        valor = df_produto['Valor da venda'].value_counts().index[0]
        forma_pgto = df_produto['Forma de pagamento'].value_counts().index[0]

        data_debit = df_produto['Data do débito'].value_counts().index[0]
        data_d1 = str(data_debit).split(' ')[0].split('-')[0]
        data_d2 = str(data_debit).split(' ')[0].split('-')[1]
        data_d3 = str(data_debit).split(' ')[0].split('-')[2]
        data_d = f'{data_d3}/{data_d2}/{data_d1}'
    
        col1.metric('Data da venda', data_metric)
        col2.metric('Valor', f'R$ {valor:,.2f}')
        col3.metric('Forma de pagamento', forma_pgto)
        col4.metric('Data do débito', data_d)

        quantidade_semanas = df_produto['Quantidade de semanas'].value_counts().index[0]
        
        if forma_pgto == 'Desconto em folha':
            if quantidade_semanas != 0:
                val_pal = valor/quantidade_semanas
                col3.metric('Quantidade de semanas', quantidade_semanas)
                col4.metric('Valor da parcela', f'R${val_pal:,.2f}')
                pagamento = {'Cliente' : clientes,
                             'Quantidade' : produto,
                             'Valor' : val_pal,
                             'Forma pagamento' : forma_pgto}
            
        else:
            pagamento = {'Cliente' : clientes,
                         'Quantidade' : produto,
                         'Valor' : valor,
                         'Forma pagamento' : forma_pgto}

        baixa_no_pagamento = col1.button('Confirmar pagamento')
        if baixa_no_pagamento:
            tempo_agora = datetime.now(fuso_horario_brasilia)
            data_utc = tempo_agora
            if isinstance(data_utc, datetime):
                data_brasilia = data_utc.astimezone(fuso_horario_brasilia)
                tempo_agora = data_brasilia.strftime('%d/%m/%Y')
            pagamento.update({'Data do pagamento' : tempo_agora})
            coll3.insert_many([pagamento])

        log_atendimento = coll3.find({'Quantidade' : produto, 'Cliente' : clientes})

        log_atendimentodf = []
        for item in log_atendimento:
               log_atendimentodf.append(item)

        container = st.container(border=True)
        with container:
            if log_atendimentodf == []:
                pass
            else:
                pd.DataFrame(log_atendimentodf)[['Data do pagamento','Forma pagamento', 'Valor']]
                 
    if cat == 3:
        #hist_3 = st.session_state['hist_3']
        #nome = hist_3['Cliente'].value_counts().index
        #cliente = st.selectbox('Cliente', nome)
        #df_cliente = hist_3[hist_3['Cliente'] == cliente]
        #df_cliente
        prod = df_motoca_3['Moto'].value_counts().index
        produto = st.selectbox('Moto', prod)
        df_produto = df_motoca_3[df_motoca_3['Moto'] == produto]
    
        col1,col2,col3,col4,col5 = st.columns(5)

        datetime_obj = datetime.strptime(df_produto['Data da venda'].value_counts().index[0], '%d/%m/%Y %H:%M')
        data1 = str(datetime_obj).split(' ')[0].split('-')[0]
        data2 = str(datetime_obj).split(' ')[0].split('-')[1]
        data3 = str(datetime_obj).split(' ')[0].split('-')[2]
        data_metric = f'{data3}/{data2}/{data1}'

        quantidade = df_produto['Quantidade de dias'].value_counts().index[0]
        valor = df_produto['Valor do aluguel'].value_counts().index[0]
        forma_pgto = df_produto['Forma de pagamento'].value_counts().index[0]

        data_debit = df_produto['Data do débito'].value_counts().index[0]
        data_d1 = str(data_debit).split(' ')[0].split('-')[0]
        data_d2 = str(data_debit).split(' ')[0].split('-')[1]
        data_d3 = str(data_debit).split(' ')[0].split('-')[2]
        data_d = f'{data_d3}/{data_d2}/{data_d1}'
    
        col1.metric('Data do aluguel', data_metric)
        col2.metric('Quantidade de dias', quantidade)
        col3.metric('Valor', f'R$ {valor:,.2f}')
        col4.metric('Forma de pagamento', forma_pgto)
        col5.metric('Data do débito', data_d)

        quantidade_semanas = df_produto['Quantidade de semanas'].value_counts().index[0]
        
        if forma_pgto == 'Desconto em folha':
            if quantidade_semanas != 0:
                val_pal = valor/quantidade_semanas
                col3.metric('Quantidade de semanas', quantidade_semanas)
                col4.metric('Valor da parcela', f'R${val_pal:,.2f}')
                pagamento = {'Cliente' : clientes,
                             'Moto' : produto,
                             'Valor' : val_pal,
                             'Forma pagamento' : forma_pgto}
            
        else:
            pagamento = {'Cliente' : clientes,
                         'Moto' : produto,
                         'Valor' : valor,
                         'Forma pagamento' : forma_pgto}

        baixa_no_pagamento = col1.button('Confirmar pagamento')
        if baixa_no_pagamento:
            tempo_agora = datetime.now(fuso_horario_brasilia)
            data_utc = tempo_agora
            if isinstance(data_utc, datetime):
                data_brasilia = data_utc.astimezone(fuso_horario_brasilia)
                tempo_agora = data_brasilia.strftime('%d/%m/%Y')
            pagamento.update({'Data do pagamento' : tempo_agora})
            coll3.insert_many([pagamento])

        log_atendimento = coll3.find({'Moto' : produto, 'Cliente' : clientes})

        log_atendimentodf = []
        for item in log_atendimento:
               log_atendimentodf.append(item)

        container = st.container(border=True)
        with container:
            if log_atendimentodf == []:
                pass
            else:
                pd.DataFrame(log_atendimentodf)[['Data do pagamento','Forma pagamento', 'Valor']]

    if cat == 4:
        #nome = hist_1['Cliente'].value_counts().index
        #cliente = st.selectbox('Cliente', nome)
        #df_cliente = hist_1[hist_1['Cliente'] == cliente]
        #df_cliente
        prod = df_motoca_4['_id'].value_counts().index
        produto = st.selectbox('OS.', prod)
        df_produto = df_motoca_4[df_motoca_4['_id'] == produto]

        item = []

        for i in df_produto['Venda']:    
            item.append(i)
            df_itens = pd.DataFrame(item[0], columns= ['Produto','Quantidade', 'Valor'])
        
        col1,col2,col3,col4 = st.columns(4)

        datetime_obj = datetime.strptime(df_produto['Data da venda'].value_counts().index[0], '%d/%m/%Y %H:%M')
        data1 = str(datetime_obj).split(' ')[0].split('-')[0]
        data2 = str(datetime_obj).split(' ')[0].split('-')[1]
        data3 = str(datetime_obj).split(' ')[0].split('-')[2]
        data_metric = f'{data3}/{data2}/{data1}'

        valor = df_produto['Valor'].value_counts().index[0]
        forma_pgto = df_produto['Forma de pagamento'].value_counts().index[0]

        data_debit = df_produto['Data do débito'].value_counts().index[0]
        data_d1 = str(data_debit).split(' ')[0].split('-')[0]
        data_d2 = str(data_debit).split(' ')[0].split('-')[1]
        data_d3 = str(data_debit).split(' ')[0].split('-')[2]
        data_d = f'{data_d3}/{data_d2}/{data_d1}'
    
        col1.metric('Data da venda', data_metric)
        col2.markdown('Produtos')
        col2.dataframe(df_itens)
        col3.metric('Mecânico', df_motoca_4['Mecanico'].values[0])
        col4.metric('Valor', f'R$ {valor:,.2f}')
        col1.metric('Forma de pagamento', forma_pgto)
        col3.metric('Data do débito', data_d)

        if forma_pgto == 'Desconto em folha':
            quantidade_semanas = df_produto['Quantidade de semanas'].value_counts().index[0]
    
            if quantidade_semanas != 0:
                val_pal = valor/quantidade_semanas
                col3.metric('Quantidade de semanas', quantidade_semanas)
                col4.metric('Valor da parcela', f'R${val_pal:,.2f}')
                pagamento = {'Cliente' : clientes,
                             'Produto' : produto,
                             'Valor' : val_pal,
                            'Forma pagamento' : forma_pgto}
            
        else:
            pagamento = {'Cliente' : clientes,
                         'Produto' : produto,
                         'Valor' : valor,
                         'Forma pagamento' : forma_pgto}          

        baixa_no_pagamento = col1.button('Confirmar pagamento')
        if baixa_no_pagamento:
            tempo_agora = datetime.now(fuso_horario_brasilia)
            data_utc = tempo_agora
            if isinstance(data_utc, datetime):
                data_brasilia = data_utc.astimezone(fuso_horario_brasilia)
                tempo_agora = data_brasilia.strftime('%d/%m/%Y')
            pagamento.update({'Data do pagamento' : tempo_agora})
            coll3.insert_many([pagamento])
        
        log_atendimento = coll3.find({'Produto' : produto, 'Cliente' : clientes})

        log_atendimentodf = []
        for item in log_atendimento:
               log_atendimentodf.append(item)

        container = st.container(border=True)
        with container:
            if log_atendimentodf == []:
                pass
            else:
                pd.DataFrame(log_atendimentodf)[['Data do pagamento','Forma pagamento', 'Valor']]

def pagina_principal():
    col1,col2 = st.columns(2)
    col1.title('**BOX Comodoro**')
    col2.image('files/WhatsApp Image 2025-01-04 at 11.51.06.jpeg', width=200)

    btn = authenticator.logout()
    if btn:
        st.session_state["authentication_status"] == None
    st.divider()
    pesquisa_pgto()

def main():
    if st.session_state["authentication_status"]:
        pagina_principal()
  
    elif st.session_state["authentication_status"] == False:
        st.error("Username/password is incorrect.")

    elif st.session_state["authentication_status"] == None:
        st.warning("Please insert username and password")

if __name__ == '__main__':
    main()