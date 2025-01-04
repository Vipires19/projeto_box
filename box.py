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

st.set_page_config(
            layout =  'wide',
            page_title = 'Comodoro Delivery',
        )

st.logo('files/LOGO.png', icon_image='files/WhatsApp Image 2025-01-04 at 11.51.06.jpeg')


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

def deletando_produtos():
    estoque = st.session_state['estoque']
    col1,col2,col3,col4,col5,col6 = st.columns(6)
    op = ['Editar', 'Apagar']
    opcoes = col1.selectbox('Opções', op)
    cod = estoque['Código'].value_counts().index

    if opcoes == 'Editar':
        codigo = col2.selectbox('Cód', cod)
        if codigo == 1:
            df_cod = estoque[estoque['Código'] == codigo]
            produto = df_cod['Produto'].value_counts().index
            prod = col3.selectbox('Prod.', produto)
            
            campo = ['Produto', 'Quantidade', 'Valor de compra']
            campos = col4.selectbox('Selecione o campo para editar', campo)
            if campos == 'Produto':
                entry = col5.text_input('Novo produto')
            if campos == 'Quantidade':
                entry = col5.number_input('Nova quantidade', min_value=0)
            if campos == 'Valor de compra':
                entry = col5.number_input('Novo Valor')
            edita_produto = col6.button('Editar')
            if edita_produto:
                coll.update_one({'Produto': prod}, {'$set' : {campos : entry}})
    
    
    if opcoes == 'Apagar':
        codigo = col2.selectbox('Cód', cod)
        if codigo == 3:
            df_cod = estoque[estoque['Código'] == codigo]
            produto = df_cod['Moto'].value_counts().index
            bike = col3.selectbox('Moto', produto)
            edita_produto = col4.button('Apagar')
            if edita_produto:
                coll.delete_one({'Moto': bike})
        else:        
            df_cod = estoque[estoque['Código'] == codigo]
            produto = df_cod['Produto'].value_counts().index
            prod = col3.selectbox('Prod.', produto)
            edita_produto = col4.button('Apagar')
            if edita_produto:
                coll.delete_one({'Produto': prod})

def efetuando_vendas():
    cadastro = coll4.find({})
    clientesdf = []
    for item in cadastro:
        clientesdf.append(item)
    
    clientesdf = pd.DataFrame(clientesdf, columns= ['_id', 'nome'])
    clientesdf.drop(columns='_id', inplace=True)
    
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
        nome = clientesdf['nome'].value_counts().index
        cliente = col5.selectbox('Nome do cliente', nome)
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
        quantidade = col3.number_input('Quantidade.', min_value = 1, max_value=1)
        data_vale = col4.date_input('Data do vale', format='DD.MM.YYYY')
        valor_vale = col5.number_input('Valor do vale em R$')
        total = quantidade * valor_vale
        nome = clientesdf['nome'].value_counts().index
        cliente = col6.selectbox('Nome do cliente', nome)
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
            
        finalsell = estoque_2[estoque_2['Produto'] == produto][['Quantidade']].values[0] - quantidade
        
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
        nome = clientesdf['nome'].value_counts().index
        cliente = col6.selectbox('Nome do cliente', nome)
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

    st.divider()
    
    st.markdown('Cadastro de novos clientes')
    nome_cliente = st.text_input('Nome cliente:')
    col1,col2,col3,col4,col5,col6 = st.columns(6)
    cadastrar = col1.button('Cadastrar')
    if cadastrar:
        coll4.insert_many([{'nome' : nome_cliente}])
    deletar = col2.button('Excluir')
    if deletar:
        coll4.delete_one({'nome' : nome_cliente})

def atualizando_quantidade():
    estoque = st.session_state['estoque']
    estoque = estoque[['Produto', 'Quantidade']]
    for value in estoque['Quantidade']:
        if value == 0:
            produto = estoque[estoque['Quantidade'] == value]['Produto']
            for prod in produto:
                coll.delete_one({'Produto': prod})
        if value != 0:
            pass

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

    oss = db.servicos.find({})
    df_os = []
    for item in oss:
        df_os.append(item)

    df = pd.DataFrame(venda_df)
    
    df = df[['Código','Quantidade','Data da venda', 'Cliente', 'Forma de pagamento', 'Produto' ,'Data do vale', 'Valor da venda',
              'Data do débito', 'Quantidade de semanas', 'Moto', 'Quantidade de dias',
              'Data do aluguel', 'Valor do aluguel', 'Valor', '_id', 'Venda', 'Mecanico']]
    
    st.session_state['hist_full'] = df
    
    hist_1 = df[df['Código'] == 1][['Data da venda', 'Produto' ,'Quantidade', 'Cliente', 'Valor da venda', 'Forma de pagamento', 'Data do débito', 'Quantidade de semanas']]
    hist_1['Quantidade de semanas'] = hist_1['Quantidade de semanas'].fillna(0)
    st.session_state['hist_1'] = hist_1

    hist_2 = df[df['Código'] == 2][['Data da venda', 'Produto' , 'Quantidade', 'Data do vale', 'Cliente', 'Valor da venda', 'Forma de pagamento', 'Data do débito', 'Quantidade de semanas']]
    hist_2['Quantidade de semanas'] = hist_2['Quantidade de semanas'].fillna(0)
    st.session_state['hist_2'] = hist_2
    
    hist_3 = df[df['Código'] == 3][['Data da venda', 'Produto' , 'Moto', 'Cliente','Data do aluguel', 'Quantidade de dias', 'Valor do aluguel', 
                                    'Forma de pagamento', 'Data do débito', 'Quantidade de semanas']]
    hist_3['Quantidade de semanas'] = hist_3['Quantidade de semanas'].fillna(0)
    st.session_state['hist_3'] = hist_3

    hist_4 = df[df['Código'] == 4][['Data da venda', 'Valor', 'Cliente', 'Mecanico', 'Forma de pagamento', 'Data do débito', 'Quantidade de semanas', '_id']]
    hist_4['Quantidade de semanas'] = hist_4['Quantidade de semanas'].fillna(0)
    st.session_state['hist_4'] = hist_4

    filtro_hist = st.selectbox('Filtro', ['Diário', 'Geral'])


    if filtro_hist == 'Diário':

        col1,col2,col3 = st.columns(3)
        dia = col1.number_input('Pesquisa Dia', min_value=1, max_value=31)
        mes = str(col2.number_input('Pesquisa Mês', min_value=1, max_value=12))
        ano = str(col3.number_input('Pesquisa Ano', min_value=2024, max_value=2030))
        if dia <= 9:
            dia = f'0{dia}'
        if mes <= '9':
            mes = f'0{mes}'
        data_pesquisa = f'{ano}-{mes}-{dia}'
    
        st.header('**Venda de produtos**')

        produtos = hist_1[hist_1['Data do débito'] == data_pesquisa]
        if produtos['Quantidade'].empty:
            st.markdown('Não há vendas para data selecionada')
        else:
            produtos
    
        st.header('**Vales/Antecipações**')

        vales = hist_2[hist_2['Data do débito'] == data_pesquisa]
        if vales['Quantidade'].empty:
            st.markdown('Não há vales para data selecionada')
        else:
            vales
    
        st.header('**Aluguel de motos**')

        motos = hist_3[hist_3['Data do aluguel'] == data_pesquisa]
        if motos['Moto'].empty:
            st.markdown('Não há aluguéis para data selecionada')
        else:
            motos

        st.header('**Ordens de serviço**')

        manutencao = hist_4[hist_4['Data do débito'] == data_pesquisa]
        if manutencao['_id'].empty:
            st.markdown('Não há ordens de serviço para data selecionada')
        else:
            manutencao

    if filtro_hist == 'Geral':
        st.header('**Venda de produtos**')
        hist_1

        st.header('**Vales/Antecipações**')
        hist_2

        st.header('**Aluguel de motos**')
        hist_3

        st.header('**Ordens de serviço**')
        hist_4

    col1,col2,col3 = st.columns(3)
    pessoa = df['Cliente'].value_counts().index
    cliente = col1.selectbox('Cliente', pessoa)
    df_cliente = df[df['Cliente'] == cliente]
    data = df_cliente['Data da venda'].value_counts().index
    data_venda = col2.selectbox('Data da venda', data)
    deleta_venda = col3.button('Deletar')
    if deleta_venda:
        coll2.delete_one({'Cliente': cliente,
                         'Data da venda' : data_venda})    

def pesquisa_pgto():
    df = st.session_state['hist_full']
    fuso_horario_brasilia = pytz.timezone("America/Sao_Paulo")
    cliente = df['Cliente'].value_counts().index
    clientes = st.selectbox('Motoca', cliente)
    df_motoca = df[df['Cliente'] == clientes]
    df_motoca_1 = df_motoca[df_motoca['Código'] == 1][['Data da venda', 'Produto' ,'Quantidade', 'Valor da venda', 'Forma de pagamento', 'Data do débito', 'Quantidade de semanas']]
    df_motoca_2 = df_motoca[df_motoca['Código'] == 2][['Data da venda', 'Data do vale', 'Valor da venda', 'Forma de pagamento', 'Data do débito', 'Quantidade de semanas']]
    df_motoca_3 = df_motoca[df_motoca['Código'] == 3][['Data da venda', 'Produto' , 'Moto', 'Data do aluguel', 'Quantidade de dias', 'Valor do aluguel', 'Forma de pagamento', 'Data do débito', 'Quantidade de semanas']]
    col1,col2,col3 = st.columns(3)
    col1.header('Produtos')
    col1.dataframe(df_motoca_1)
    col2.header('Vale/Antecipação')
    col2.dataframe(df_motoca_2)
    col3.header('Aluguel Moto')
    col3.dataframe(df_motoca_3)

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

def pagina_principal():
    col1,col2 = st.columns(2)
    col1.title('**BOX Comodoro**')
    col2.image('files/WhatsApp Image 2025-01-04 at 11.51.06.jpeg', width=200)

    btn = authenticator.logout()
    if btn:
        st.session_state["authentication_status"] == None

    tab1,tab2,tab3 = st.tabs(['Estoque', 'Vendas','Histórico de Vendas'])#, 'Pagamento'])

    tab1.title('Estoque')
    
    with tab1:
        inserindo_dados()
        st.divider()
        deletando_produtos()
                
    tab2.title('Vendas')

    with tab2:
        efetuando_vendas()
           
    tab3.title('Histórico de vendas')
    
    with tab3:
        historico_vendas()

    #tab4.title('Pagamento')

    #with tab4:
    #    pesquisa_pgto()

    atualizando_quantidade()
            
def main():
    if st.session_state["authentication_status"]:
    
        pagina_principal()
  
    elif st.session_state["authentication_status"] == False:
        st.error("Username/password is incorrect.")

    elif st.session_state["authentication_status"] == None:
        st.warning("Please insert username and password")

if __name__ == '__main__':

    main()
