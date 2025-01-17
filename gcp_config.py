#%%
import streamlit as st
from google.oauth2 import service_account
from google.cloud import bigquery

credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])
client = bigquery.Client(project="dw-fin", 
                         credentials=credentials)

def dataset():
    dataset = bigquery.Dataset("dw-fin.pif_project")
    client.create_dataset(dataset)

def game_table():
    schema = [
        bigquery.SchemaField('id_jogo', 'STRING', mode='REQUIRED')
        , bigquery.SchemaField('data_jogo', 'DATE', mode='NULLABLE')
        , bigquery.SchemaField('participantes', 'INT64', mode='NULLABLE')
        , bigquery.SchemaField('inicio', 'STRING', mode='NULLABLE')
        , bigquery.SchemaField('fim', 'STRING', mode='NULLABLE')
        , bigquery.SchemaField('tempo', 'STRING', mode='NULLABLE')
        , bigquery.SchemaField('buyin', 'NUMERIC', mode='NULLABLE')
        , bigquery.SchemaField('stack_inicial', 'INT64', mode='NULLABLE')
    ]

    table = bigquery.Table("dw-fin.pif_project.game_table", schema)
    client.create_table(table)

def playa_table():
    schema = [
        bigquery.SchemaField('id_jogo', 'STRING', mode='REQUIRED')
        , bigquery.SchemaField('id_player', 'INT64', mode='NULLABLE')
        , bigquery.SchemaField('player', 'STRING', mode='NULLABLE')
        , bigquery.SchemaField('rebuys', 'INT64', mode='NULLABLE')
        , bigquery.SchemaField('stack_final', 'INT64', mode='NULLABLE')
        , bigquery.SchemaField('tempo_jogo', 'STRING', mode='NULLABLE')
        , bigquery.SchemaField('pago', 'NUMERIC', mode='NULLABLE')
        , bigquery.SchemaField('ganho', 'NUMERIC', mode='NULLABLE')
        , bigquery.SchemaField('saldo', 'NUMERIC', mode='NULLABLE')
    ]

    table = bigquery.Table("dw-fin.pif_project.players_table", schema)
    client.create_table(table)

def insert(df):
    tipo = len(df.columns)

    if tipo == 8:
        '''game_table'''
    elif tipo == 9:
        '''playa_table'''


