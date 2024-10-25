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

st.set_page_config(
            layout =  'wide',
            page_title = 'Comodoro Delivery',
        )


# --- Authentication ---
# Load hashed passwords
file_path = Path('comodoro.py').parent/"db"/"hashed_pw.pkl"

with file_path.open("rb") as file:
  hashed_passwords = pickle.load(file)
  
credentials = {
    "usernames": {
        "admin": {
            "name": "Admin",
            "password": hashed_passwords[0]
        }
    }
}


authenticator = stauth.Authenticate(credentials= credentials, cookie_name="st_session", cookie_key="key123", cookie_expiry_days= 1)
authenticator.login()

def inserindo_dados():
    col1,col2,col3,col4,col5 = st.columns(5)
    codigo = col1.number_input('Código do Produto', min_value = 1, max_value = 3)
    if codigo == 1:
        nome = col2.text_input('Nome do Produto')
        quantidade = col3.number_input('Quant.', min_value = 0, max_value = 100000)
        valor_compra = col4.number_input('Valor de Compra em R$')
        adiciona_produto = col5.button('Adicionar')
        if adiciona_produto:
            entry = [{'Código' : codigo, 'Produto': nome, 'Quantidade' : quantidade, 'Valor de compra' : valor_compra}]
            result = coll.insert_many(entry)
    
    if codigo == 2:
        nome = ['Vale/Antecipação']
        nome1 = col2.selectbox('Nome do Produto', nome)
        quantidade = col3.number_input('Quant.', min_value = 0, max_value = 100000)
        adiciona_produto = col4.button('Adicionar')
        if adiciona_produto:
            entry = [{'Código' : codigo, 'Produto': nome1, 'Quantidade' : quantidade}]
            result = coll.insert_many(entry)
    

    if codigo == 3:
        nome = ['Aluguel Moto']
        nome1 = col2.selectbox('Nome do Produto', nome)
        placa = col3.text_input('Placa da moto', placeholder= 'EX: ABC-3A30')
        quantidade = col4.number_input('Quant.', min_value = 1, max_value = 1)
        valor_compra = 0
        adiciona_produto = col5.button('Adicionar')
        if adiciona_produto:
            entry = [{'Código' : codigo, 'Produto': nome1, 'Placa' : placa, 'Quantidade' : quantidade, 'Valor de compra' : valor_compra}]
            result = coll.insert_many(entry)
    
    estoque1 = db.estoque.find({})
    estoquedf = []
    for item in estoque1:
        estoquedf.append(item)

    
    df = pd.DataFrame(estoquedf, columns= ['_id', 'Código', 'Produto', 'Placa','Quantidade', 'Valor de compra'])
    df.drop(columns='_id', inplace=True)
    estoque = df
    estoque_1 = df[df['Código'] == 1][['Código', 'Produto', 'Quantidade', 'Valor de compra']]
    estoque_2 = df[df['Código'] == 2][['Código', 'Produto', 'Quantidade']]
    estoque_3 = df[df['Código'] == 3][['Código', 'Produto', 'Placa']]
    col1,col2,col3 = st.columns(3)
    col1.dataframe(estoque_1)
    col2.dataframe(estoque_2)
    col3.dataframe(estoque_3)
    
    st.session_state['estoque'] = estoque
    st.session_state['estoque_1'] = estoque_1
    st.session_state['estoque_2'] = estoque_2
    st.session_state['estoque_3'] = estoque_3

def efetuando_vendas():

    estoque = st.session_state['estoque']
    estoque_1 = st.session_state['estoque_1']
    estoque_2 = st.session_state['estoque_2']
    estoque_3 = st.session_state['estoque_3']
    fuso_horario_brasilia = pytz.timezone("America/Sao_Paulo")

    col1,col2,col3,col4, col5,col6,col7,col8= st.columns(8)

    cod = estoque['Código'].value_counts().index
    codigo = col1.selectbox('Código', cod)

    if codigo == 1:
        prod = estoque_1['Produto'].value_counts().index
        produto = col2.selectbox('Produto', prod)
        quantidade = col3.number_input('Quant.', min_value = 0, max_value = 100000, key="input_quantidade_venda")
        valor_venda = col4.number_input('Valor de venda em R$' )
        total = quantidade * valor_venda
        valor_total = col4.metric('Valor total', f'R$ {total:,.2f}')
        cliente = col5.text_input('Nome do cliente')
        pagamento = ['Pix', 'Cartão de crédito', 'Dinheiro', 'Desconto em folha']
        forma_pagamento = col6.selectbox('Forma de pagamento', pagamento)
        data_debito = col7.date_input('Data do débito', format='DD.MM.YYYY')
        tempo_agora = datetime.now(fuso_horario_brasilia)
        

        if forma_pagamento == 'Desconto em folha':
            quantidade_semanas = col8.number_input('Quantidade de semana', min_value= 0)
            sell = {'Código' : codigo,
                    'Produto' : produto,
                    'Quantidade' : quantidade,
                    'Valor da venda' : total,
                    'Cliente' : cliente,
                    'Forma de pagamento' : forma_pagamento,
                    'Data do débito' : str(data_debito),
                    'Quantidade de semanas' : quantidade_semanas}
            
                
        else:
            sell = {'Código' : codigo,
                    'Produto' : produto,
                    'Quantidade' : quantidade,
                    'Valor da venda' : total,
                    'Cliente' : cliente,
                    'Forma de pagamento' : forma_pagamento,
                    'Data do débito' : str(data_debito)}
            
        finalsell = estoque_1[estoque_1['Produto'] == produto][['Quantidade']].values - quantidade
        vende_produto = col8.button('Concluir Venda')     
        if vende_produto:
            tempo_agora = datetime.now(fuso_horario_brasilia)
            data_utc = tempo_agora
            if isinstance(data_utc, datetime):
                data_brasilia = data_utc.astimezone(fuso_horario_brasilia)
                tempo_agora = data_brasilia.strftime('%d/%m/%Y %H:%M')            
            sell.update({'Data da venda' : tempo_agora})
            coll2.insert_many([sell])
            coll.update_one({'Produto': produto}, {'$set' : {'Quantidade' : int(finalsell)}})
        
        estoque_1

    if codigo == 2:
        prod = estoque_2['Produto'].value_counts().index
        produto = col2.selectbox('Produto', prod)
        quantidade = col3.number_input('Quantidade.', min_value = 1)
        data_vale = col4.date_input('Data do vale', format='DD.MM.YYYY')
        valor_vale = col5.number_input('Valor do vale em R$')
        total = quantidade * valor_vale
        cliente = col6.text_input('Nome do cliente')
        pagamento = ['Pix', 'Cartão de crédito', 'Dinheiro', 'Desconto em folha']
        forma_pagamento = col7.selectbox('Forma de pagamento', pagamento)
        data_debito = col8.date_input('Data do débito', format='DD.MM.YYYY')

        if forma_pagamento == 'Desconto em folha':
            quantidade_semanas = col8.number_input('Quantidade de semana', min_value= 0)
            sell = {'Código' : codigo,
                    'Produto' : produto,
                    'Quantidade' : quantidade,
                    'Data do vale' : str(data_vale),
                    'Valor da venda' : total,
                    'Cliente' : cliente,
                    'Forma de pagamento' : forma_pagamento,
                    'Data do débito' : str(data_debito),
                    'Quantidade de semanas' : quantidade_semanas}
            
                
        else:
            sell = {'Código' : codigo,
                    'Produto' : produto,
                    'Quantidade' : quantidade,
                    'Data do vale' : str(data_vale),
                    'Valor da venda' : total,
                    'Cliente' : cliente,
                    'Forma de pagamento' : forma_pagamento,
                    'Data do débito' : str(data_debito)}
            
        finalsell = estoque_2[estoque_2['Produto'] == produto][['Quantidade']].values - quantidade
        vende_produto = col8.button('Concluir Venda')     
        if vende_produto:
            tempo_agora = datetime.now(fuso_horario_brasilia)
            data_utc = tempo_agora
            if isinstance(data_utc, datetime):
                data_brasilia = data_utc.astimezone(fuso_horario_brasilia)
                tempo_agora = data_brasilia.strftime('%d/%m/%Y %H:%M')
            sell.update({'Data da venda' : tempo_agora})
            coll2.insert_many([sell])
            coll.update_one({'Produto': produto}, {'$set' : {'Quantidade' : int(finalsell)}})
            
        estoque_2

    if codigo == 3:
        prod = estoque_3['Produto'].value_counts().index
        produto = col2.selectbox('Produto', prod)
        bike = estoque_3['Placa'].value_counts().index
        moto = col2.selectbox('Moto', bike)
        quantidade = col3.number_input('Quantidade de dias', min_value = 1)
        data_aluguel = col4.date_input('Data do Aluguel', format='DD.MM.YYYY')
        valor_diaria = col5.number_input('Valor da diaria em R$')
        total = quantidade * valor_diaria
        valor_total = col5.metric('Valor total', f'R$ {total:,.2f}')
        cliente = col6.text_input('Nome do cliente')
        pagamento = ['Pix', 'Cartão de crédito', 'Dinheiro', 'Desconto em folha']
        forma_pagamento = col7.selectbox('Forma de pagamento', pagamento)
        data_debito = col8.date_input('Data do débito', format='DD.MM.YYYY')

        if forma_pagamento == 'Desconto em folha':
            quantidade_semanas = col8.number_input('Quantidade de semana', min_value= 0)
            sell = {'Código' : codigo,
                    'Produto' : produto,
                    'Moto' : moto,
                    'Quantidade' : 1,
                    'Quantidade de dias' : quantidade,
                    'Data do aluguel' : str(data_aluguel),
                    'Valor do aluguel' : total,
                    'Cliente' : cliente,
                    'Forma de pagamento' : forma_pagamento,
                    'Data do débito' : str(data_debito),
                    'Quantidade de semanas' : quantidade_semanas}
            
                
        else:
            sell = {'Código' : codigo,
                    'Produto' : produto,
                    'Moto' : moto,
                    'Quantidade' : 1,
                    'Quantidade de dias' : quantidade,
                    'Data do aluguel' : str(data_aluguel),
                    'Valor do aluguel' : total,
                    'Cliente' : cliente,
                    'Forma de pagamento' : forma_pagamento,
                    'Data do débito' : str(data_debito)}
            
        #finalsell = estoque_3[estoque_3['Produto'] == produto][['Quantidade']].values - quantidade
        vende_produto = col8.button('Concluir Venda')     
        if vende_produto:
            tempo_agora = datetime.now(fuso_horario_brasilia)
            data_utc = tempo_agora
            if isinstance(data_utc, datetime):
                data_brasilia = data_utc.astimezone(fuso_horario_brasilia)
                tempo_agora = data_brasilia.strftime('%d/%m/%Y %H:%M')
            sell.update({'Data da venda' : tempo_agora})
            coll2.insert_many([sell])
            coll.delete_one({'Placa': moto})
            
        estoque_3    

def historico_vendas():
    venda1 = db.Vendas.find({})
    fuso_horario_brasilia = pytz.timezone("America/Sao_Paulo")
    venda_df = []
    for item in venda1:
        venda_df.append(item)
        # Ajustar o horário armazenado em UTC para o horário de Brasília
        if 'Data da venda' in item:
            data_utc = item['Data da venda']
            if isinstance(data_utc, datetime):
                data_brasilia = data_utc.astimezone(fuso_horario_brasilia)
                item['Data da venda'] = data_brasilia.strftime('%d/%m/%Y %H:%M')
    
    df = pd.DataFrame(venda_df)
    df.drop(columns='_id', inplace=True)
    df = df[['Código','Quantidade','Data da venda', 'Cliente', 'Forma de pagamento', 'Produto' ,'Data do vale', 'Valor da venda',
              'Data do débito', 'Quantidade de semanas', 'Moto', 'Quantidade de dias',
              'Data do aluguel', 'Valor do aluguel']]
    
    st.markdown('**Venda de artigos**')
    hist_1 = df[df['Código'] == 1][['Data da venda', 'Produto' ,'Quantidade', 'Cliente', 'Valor da venda', 'Forma de pagamento', 'Data do débito', 'Quantidade de semanas']]
    hist_1['Quantidade de semanas'] = hist_1['Quantidade de semanas'].fillna(0)
    
    hist_1
    st.session_state['hist_1'] = hist_1

    st.markdown('**Vales/Antecipações**')
    hist_2 = df[df['Código'] == 2][['Data da venda', 'Produto' , 'Quantidade', 'Data do vale', 'Cliente', 'Valor da venda', 'Forma de pagamento', 'Data do débito', 'Quantidade de semanas']]
    hist_2['Quantidade de semanas'] = hist_2['Quantidade de semanas'].fillna(0)

    hist_2
    st.session_state['hist_2'] = hist_2

    st.markdown('**Aluguel de motos**')
    hist_3 = df[df['Código'] == 3][['Data da venda', 'Produto' , 'Moto', 'Cliente','Data do aluguel', 'Quantidade de dias', 'Valor do aluguel', 
                                    'Forma de pagamento', 'Data do débito', 'Quantidade de semanas']]
    hist_3['Quantidade de semanas'] = hist_3['Quantidade de semanas'].fillna(0)

    hist_3
    st.session_state['hist_3'] = hist_3

    st.session_state['hist_full'] = df

def pesquisa_pgto():
    fuso_horario_brasilia = pytz.timezone("America/Sao_Paulo")
    categoria = ['Artigos', 'Vale/Antecipação', 'Aluguel']
    cat = st.selectbox('Categoria', categoria)
    if cat == 'Artigos':
        hist_1 = st.session_state['hist_1']
        nome = hist_1['Cliente'].value_counts().index
        cliente = st.selectbox('Cliente', nome)
        df_cliente = hist_1[hist_1['Cliente'] == cliente]
        df_cliente
        prod = df_cliente['Produto'].value_counts().index
        produto = st.selectbox('Prod.', prod)
        df_produto = df_cliente[df_cliente['Produto'] == produto]
        
    
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
        data_d = f'{data3}/{data2}/{data1}'
    
        col1.metric('Data da venda', data_metric)
        col2.metric('Produto', produto )
        col3.metric('Quantidade', quantidade)
        col4.metric('Valor', f'R$ {valor:,.2f}')
        col1.metric('Forma de pagamento', forma_pgto)
        col2.metric('Data do débito', data_d)

        quantidade_semanas = df_produto['Quantidade de semanas'].value_counts().index[0]
    
        if quantidade_semanas != 0:
            val_pal = valor/quantidade_semanas
            col3.metric('Quantidade de semanas', quantidade_semanas)
            col4.metric('Valor da parcela', f'R${val_pal:,.2f}')
            pagamento = {'Cliente' : cliente,
                         'Produto' : produto,
                         'Valor' : val_pal,
                        'Forma pagamento' : forma_pgto}
            
        else:
            pagamento = {'Cliente' : cliente,
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
        
        log_atendimento = coll3.find({'Produto' : produto, 'Cliente' : cliente})

        log_atendimentodf = []
        for item in log_atendimento:
               log_atendimentodf.append(item)

        container = st.container(border=True)
        with container:
            if log_atendimentodf == []:
                pass
            else:
                pd.DataFrame(log_atendimentodf)[['Data do pagamento','Forma pagamento', 'Valor']]

    if cat == 'Vale/Antecipação':
        hist_2 = st.session_state['hist_2']
        nome = hist_2['Cliente'].value_counts().index
        cliente = st.selectbox('Cliente', nome)
        df_cliente = hist_2[hist_2['Cliente'] == cliente]
        df_cliente
        prod = df_cliente['Quantidade'].value_counts().index
        produto = st.selectbox('Vale', prod)
        df_produto = df_cliente[df_cliente['Quantidade'] == produto]
    
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
        data_d = f'{data3}/{data2}/{data1}'
    
        col1.metric('Data da venda', data_metric)
        col2.metric('Valor', f'R$ {valor:,.2f}')
        col3.metric('Forma de pagamento', forma_pgto)
        col4.metric('Data do débito', data_d)

        quantidade_semanas = df_produto['Quantidade de semanas'].value_counts().index[0]
        
        if quantidade_semanas != 0:
            val_pal = valor/quantidade_semanas
            col3.metric('Quantidade de semanas', quantidade_semanas)
            col4.metric('Valor da parcela', f'R${val_pal:,.2f}')
            pagamento = {'Cliente' : cliente,
                         'Quantidade' : produto,
                         'Valor' : val_pal,
                         'Forma pagamento' : forma_pgto}
            
        else:
            pagamento = {'Cliente' : cliente,
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

        log_atendimento = coll3.find({'Quantidade' : produto, 'Cliente' : cliente})

        log_atendimentodf = []
        for item in log_atendimento:
               log_atendimentodf.append(item)

        container = st.container(border=True)
        with container:
            if log_atendimentodf == []:
                pass
            else:
                pd.DataFrame(log_atendimentodf)[['Data do pagamento','Forma pagamento', 'Valor']]
                 
    if cat == 'Aluguel':
        hist_3 = st.session_state['hist_3']
        nome = hist_3['Cliente'].value_counts().index
        cliente = st.selectbox('Cliente', nome)
        df_cliente = hist_3[hist_3['Cliente'] == cliente]
        df_cliente
        prod = df_cliente['Moto'].value_counts().index
        produto = st.selectbox('Moto', prod)
        df_produto = df_cliente[df_cliente['Moto'] == produto]
    
        col1,col2,col3,col4,col5 = st.columns(5)

        datetime_obj = datetime.strptime(df_produto['Data da venda'].value_counts().index[0], '%d/%m/%Y %H:%M')
        data1 = str(datetime_obj).split(' ')[0].split('-')[0]
        data2 = str(datetime_obj).split(' ')[0].split('-')[1]
        data3 = str(datetime_obj).split(' ')[0].split('-')[2]
        data_metric = f'{data3}/{data2}/{data1}'

        quantidade = df_produto['Quantidade de dias'].value_counts().index
        valor = df_produto['Valor do aluguel'].value_counts().index[0]
        forma_pgto = df_produto['Forma de pagamento'].value_counts().index[0]

        data_debit = df_produto['Data do débito'].value_counts().index[0]
        data_d1 = str(data_debit).split(' ')[0].split('-')[0]
        data_d2 = str(data_debit).split(' ')[0].split('-')[1]
        data_d3 = str(data_debit).split(' ')[0].split('-')[2]
        data_d = f'{data3}/{data2}/{data1}'
    
        col1.metric('Data do aluguel', data_metric)
        col2.metric('Quantidade de dias', quantidade)
        col3.metric('Valor', f'R$ {valor:,.2f}')
        col4.metric('Forma de pagamento', forma_pgto)
        col5.metric('Data do débito', data_d)

        quantidade_semanas = df_produto['Quantidade de semanas'].value_counts().index[0]
        
        if quantidade_semanas != 0:
            val_pal = valor/quantidade_semanas
            col3.metric('Quantidade de semanas', quantidade_semanas)
            col4.metric('Valor da parcela', f'R${val_pal:,.2f}')
            pagamento = {'Cliente' : cliente,
                         'Moto' : produto,
                         'Valor' : val_pal,
                         'Forma pagamento' : forma_pgto}
            
        else:
            pagamento = {'Cliente' : cliente,
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

        log_atendimento = coll3.find({'Moto' : produto, 'Cliente' : cliente})

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
    st.title('**BOX Comodoro**')

    btn = authenticator.logout()
    if btn:
        st.session_state["authentication_status"] == None
    
    tab1,tab2,tab3,tab4 = st.tabs(['Estoque', 'Vendas','Histórico de Vendas', 'Pagamento'])

    tab1.title('Estoque')
    
    with tab1:
        inserindo_dados()
                
    tab2.title('Vendas')

    with tab2:
        efetuando_vendas()
           
    tab3.title('Histórico de vendas')
    
    with tab3:
        historico_vendas()

    tab4.title('Pagamento')

    with tab4:
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
