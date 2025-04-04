#%%
import json
import numpy as np
import pandas as pd
import datetime as dt
import streamlit as st

# AUX GERAIS
def read_json(jeison):
    """
    Função pra ler o json

    Args:
        jeison (str): o nome do json na pasta para ler

    Returns:
        dict: o json lido
    """
    with open(jeison, 'r',encoding="utf-8") as arquivo:
        dis = json.load(arquivo)
    
    return dis


# PRE GAME
def game_information(players, buyin, fichas):
    """
    Gera 
    
    """
    data = str(dt.date.today())
    if f'game' not in st.session_state:
        st.session_state[f'game'] = {
            "players":players
            , "buyin":buyin
            , "fichas": fichas
            , 'unitario':buyin/fichas
            , "start": dt.datetime.now().strftime("%H:%M:%S")
            , "data": str(dt.date.today())
            , "id_jogo": ''.join(data.split('-'))+f'-{len(players)}'
        }
    st.session_state['status'] = 'in'


def game_status():
    if 'status' not in st.session_state:
        st.session_state['status'] = 'pre'


# IN GAME
# DESCOBRIR COMO PARAR ESSA PORRA QUANDO CLICAR NO BOTAO DE PARAR RELOGIO

rerun = 1

@st.fragment(run_every=rerun)
def game_timer(start, dia):
    global rerun
    i = dt.datetime.strptime(start, "%H:%M:%S")
    f = dt.datetime.now()
    match_time = f - i
    
    display = str(match_time).split(",")[1].split(".")[0]

    st.title(display)

    if st.session_state['status'] == 'end':
        st.session_state[f'game']['finish'] = dt.datetime.now().strftime("%H:%M:%S")
        st.session_state[f'game']['duration'] = display



def time_played():
    """
    Função para puxar o tempo jogado de cada player
    """
    start = dt.datetime.strptime(st.session_state[f'game']['start']
                                  , "%H:%M:%S")
    
    if 'time_played' not in st.session_state:
        st.session_state['time_played'] = {x:None 
                                           for x in st.session_state[f'game']['players']} 
    
    for k, v in st.session_state['in_game_changes']['edited_rows'].items():
        playa = st.session_state['game_data'].loc[int(k), "Players"]
        if "Final" in v.keys() and st.session_state['time_played'][playa] is None:
            f = dt.datetime.now()
            match_time = f - start
            st.session_state['time_played'][playa] = str(match_time).split(",")[1].split(".")[0]


def trava_end(dia):
    """
    funcao de travar o end game para garantir que todas as fichas em jogo tenha sido saidas
    """

    fichas_iniciais = len(st.session_state[f'game']['players'])
    rebuys = st.session_state['game_data']['Rebuys'].values.sum()

    fichas_totais = (fichas_iniciais + rebuys)*st.session_state[f'game']['fichas']
    
    # fichas_finais = st.session_state['game_data']['Final'].fillna(0).values.sum()
    fichas_finais = pd.to_numeric(st.session_state['game_data']['Final'], errors='coerce').fillna(0).sum()


    if fichas_totais != fichas_finais:
        return f"""Fichas finais informadas não batem com as jogadas
        \nFichas jogadas: {fichas_totais}
        \nFichas finais: {fichas_finais}""", True
    else:
        return "Para encerrar o jogo pressione o botão", False
    

# END GAME
def game_saldos(dia):
    unit = st.session_state[f'game']['unitario']
    df_outputs = pd.DataFrame([], index=st.session_state[f'game']['players'])
    df = st.session_state['game_data'].copy()
    df = df.set_index(["Players"])

    lis = []
    for jog in df.index:
        linha = df.loc[jog]        
    
        pagar = 0
        if not linha["BI Pg"]:
            pagar += st.session_state[f'game']['buyin']

        if not linha["RB Pg"] and linha["Rebuys"] > 0:
            pagar += linha["Rebuys"]*st.session_state[f'game']['buyin']
        else:
            pass

        receber = linha['Final']*unit

        saldo = receber - pagar

        lis.append((jog, pagar, receber, saldo))

    df_outputs = pd.DataFrame({ "Pagar":[x[1] for x in lis]
                               , "Receber":[y[2] for y in lis]
                               , "Saldo":[z[3] for z in lis]}
                               , index=[w[0] for w in lis])

    return df_outputs


def results(podium):
    import time
    jeison = read_json("pif_info.json")

    st.markdown("*E o grande vencedor é...*")
    time.sleep(1)

    try:
        st.image(jeison['participantes'][podium[0]]['imagem'],
                 caption="1° lugar")
    
    except:
        st.image(r"images\unknown.jpg",
                 caption="1° Lugar")


def join_tables(dia):
    """
    Função pra joinar os saldos com o game_data e o tempo jogado
    """

    saldos = game_saldos(dia)
    game_data = st.session_state['game_data'].set_index('Players')
    merge = pd.merge(game_data, saldos, left_index=True, right_index=True)
    
    if None in st.session_state['time_played'].values():
        for playa, tempo in st.session_state['time_played'].items():
            if tempo is None:
                st.session_state['time_played'][playa] = st.session_state[f'game']['duration']
    
    time = pd.DataFrame({"Tempo de Jogo":
                         st.session_state['time_played']})
    merge = pd.merge(merge, time, left_index=True, right_index=True)
    final = merge[['Rebuys', 'Final', "Pagar", 'Receber', 'Saldo', 'Tempo de Jogo']]
    final.columns = ['Rebuys', 'Fichas Finais', "Á Pagar", 'Á Receber', 'Saldo', 'Tempo de Jogo']

    return final


# DATA SAVE
def game_table(dia, comeco, fim, tempo, buyin, stack_inicial):
    """
    Gerar a tabela com os dados do jogo para o banco de dados

    Args:
        dia (str): dia do jogo no formato padrão para o app
        comeco (str): horario de inicio em formato hh:mm:ss
        fim (str): horario de fim em formato hh:mm:ss
        tempo (str): tempo de jogo em formato hh:mm:ss
        buyin (float): buyin do jogo
        stack_inicial (int): fichas iniciais para cada jogador
        
    Returns:
        pandas.DataFrame: no padrão pronto para o banco
    """
    
    data = st.session_state[f'game']['data']
    participantes = len(st.session_state[f'game']['players'])
    id_jogo = st.session_state[f'game']['id_jogo']

    tabela_jogo = pd.DataFrame({"id_jogo":id_jogo
                                , "data_jogo":data
                                , "participantes":participantes
                                , "inicio":comeco
                                , "fim":fim
                                , "tempo":tempo
                                , "buyin":buyin
                                , "stack_inicial":stack_inicial
                                }
                                , index=[0])

    return tabela_jogo


def playa_table(dia):
    """
    Gerar a tabela com as infos dos jogadores durante o jogo referente

    id_jogo
    participante
    stack_final
    rebuys
    tempo_jogo
    receber

    """
    id_jogo = st.session_state[f'game']['id_jogo']
    
    df_playa = join_tables(dia).reset_index()[['Rebuys', 'Fichas Finais', 'Á Pagar', 'Á Receber', 'Saldo', 'Tempo de Jogo', 'Players']]
    df_playa.columns = ['rebuys', 'stack_final', 'pago', 'ganho', 'saldo', 'tempo_jogo', 'player']
    df_playa['id_jogo'] = [id_jogo for i in range(len(df_playa.index))]
    df_playa['id_player'] = [read_json('pif_info.json')['participantes'][x]['id']
                             for x in df_playa.player.values]
    df_playa = df_playa[['id_jogo'
                         , 'id_player'
                         , 'player'
                         , 'rebuys'
                         , 'stack_final'
                         , 'tempo_jogo'
                         , 'pago'
                         , 'ganho'
                         , 'saldo'
                         ]]

    return df_playa


def save_game_to_cloud():
    """
    funcao pra ser acionada e lançar as tabelas geradas pelas funções anteriores para o BQ
    """
    pass

def read_tables(path='saves'):
    """
    Puxar os csv da pasta saves para dataframes organizados
    
    Parametros:
        path (str): o caminho da pasta de saves
    
    Retorna:
        games (df): Dataframe com as informações de jogo
        players (df): Dataframe com as informações dos participantes em cada jogo
    """
    import os
    dir = os.listdir(path)

    games = []
    players = []
    for arquivo in dir:
        if 'game_' in arquivo:
            path_game = os.path.join(path, arquivo)
            df = pd.read_csv(path_game)
            games.append(df)
        elif "playa_" in arquivo:
            path_jog = os.path.join(path, arquivo)
            df = pd.read_csv(path_jog)
            players.append(df)

    games = pd.concat(games, axis=0)
    players = pd.concat(players, axis=0)

    return games, players
