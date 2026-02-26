#%%
import json
import os
import uuid
import numpy as np
import pandas as pd
import datetime as dt
import streamlit as st
from google.oauth2 import service_account
from google.cloud import firestore


# AVALIAR DE REFATORAR E MANDAR ISSO PRA UMA CLASSE
# EM GCP_CONFIG QUE CONECTE MAIS FACILMENTE O BQ E FIREBASE
# Cliente Firestore (persistência em nuvem)
try:
    _credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])
    db = firestore.Client(project="dw-fin", credentials=_credentials)
except Exception:
    db = None

# Coleção de jogos ativos
POKER_GAMES_COLLECTION = "poker_games"
PIF_GAMES = "games"
PIF_PLAYERS = "players_results"


def save_game_state():
    """Salva o estado atual do jogo no Firestore usando o ID do jogo como documento."""
    if db is None or "game" not in st.session_state:
        return
    game_id = str(st.session_state["game"]["id_jogo"])
    game_data = st.session_state.get("game_data")
    game_data_dict = game_data.to_dict() if game_data is not None and hasattr(game_data, "to_dict") else {}
    data = {
        "game": st.session_state["game"],
        "status": st.session_state.get("status"),
        "game_data": game_data_dict,
        "time_played": st.session_state.get("time_played"),
        "updated_at": firestore.SERVER_TIMESTAMP,
    }

    data = prepare_for_firestore(data)

    db.collection(POKER_GAMES_COLLECTION).document(game_id).set(data)

def save_game_to_firestore(game_id, game_data, playa_data):
    game_data = prepare_for_firestore(game_data)
    playa_data = prepare_for_firestore(playa_data)

    db.collection(PIF_GAMES).document(game_id).set(game_data)
    db.collection(PIF_PLAYERS).document(game_id).set(playa_data)
    set_game_finalizado_firestore()


def _firestore_safe_key(key):
    """Garante que a chave seja string não vazia (exigência do Firestore)."""
    s = str(key).strip() if key is not None else ""
    return s if s else "_empty"


def prepare_for_firestore(data):
    """
    Transforma os dados para tipos aceitos pelo Firestore, evitando
    ValueError: One or more components is not a string or is empty.
    - Chaves de dict devem ser strings não vazias.
    - NaN/None/NA viram None (null).
    - Tipos numpy/pandas viram tipos nativos Python.
    """

    # Sentinel do Firestore: não alterar
    if hasattr(firestore, "SERVER_TIMESTAMP") and data is firestore.SERVER_TIMESTAMP:
        return data

    if data is None:
        return None

    # DataFrames e Series: convertemos para dict antes de seguir,
    # preservando a estrutura que já é usada no restante do código.
    if isinstance(data, pd.DataFrame):
        return prepare_for_firestore(data.to_dict())
    if isinstance(data, pd.Series):
        return prepare_for_firestore(data.to_dict())

    if isinstance(data, dict):
        return {
            _firestore_safe_key(k): prepare_for_firestore(v)
            for k, v in data.items()
        }
    if isinstance(data, (list, tuple)) or (hasattr(np, "ndarray") and isinstance(data, np.ndarray)):
        return [prepare_for_firestore(i) for i in data]

    # Escalares numpy/pandas
    if hasattr(np, "integer") and isinstance(data, np.integer):
        return int(data)
    if hasattr(np, "floating") and isinstance(data, np.floating):
        if np.isnan(data):
            return None
        return float(data)
    if hasattr(np, "bool_") and isinstance(data, np.bool_):
        return bool(data)
    if isinstance(data, (np.ndarray,)):
        return [prepare_for_firestore(x) for x in data.tolist()]

    # NaN / NA (Pandas e float)
    try:
        if hasattr(pd, "NA") and data is pd.NA:
            return None
        if isinstance(data, float) and np.isnan(data):
            return None
    except (TypeError, ValueError):
        pass

    # Datetime: Firestore aceita datetime; serializar como string evita problemas
    if isinstance(data, (dt.datetime, dt.date)):
        return data.isoformat() if hasattr(data, "isoformat") else str(data)

    if isinstance(data, (str, int, float, bool)):
        if isinstance(data, float) and np.isnan(data):
            return None
        return data

    # UUID ou outro objeto: string
    return str(data)

def load_last_game_firestore(game_id):
    """Busca um jogo específico no Firestore e carrega no session_state."""
    if db is None:
        return
    doc_ref = db.collection(POKER_GAMES_COLLECTION).document(str(game_id))
    doc = doc_ref.get()
    if not doc.exists:
        return
    data = doc.to_dict()
    st.session_state["game"] = data.get("game")
    st.session_state["status"] = data.get("status")
    if data.get("game_data"):
        st.session_state["game_data"] = pd.DataFrame(data["game_data"])
    if data.get("time_played") is not None:
        st.session_state["time_played"] = data["time_played"]


def load_game_state():
    """Tenta carregar um jogo ativo (não finalizado) do Firestore ao iniciar a sessão."""
    if db is None or "status" in st.session_state:
        return
    query = db.collection(POKER_GAMES_COLLECTION).where("status", "in", ["in", "end"]).limit(1)
    docs = list(query.stream())
    if not docs:
        return
    doc = docs[0]
    load_last_game_firestore(doc.id)


def set_game_finalizado_firestore():
    """Atualiza o status do documento do jogo atual para 'finalizado' no Firestore."""
    if db is None or "game" not in st.session_state:
        return print("\n\n\nNão foi possível atualizar o status do jogo\n\n\n")
    try:
        game_id = str(st.session_state["game"]["id_jogo"])
        db.collection(POKER_GAMES_COLLECTION).document(game_id).update({"status": "finalizado"})
    except Exception:
        pass

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

def save_json(dis_to_save):
    with open('game_state.json', 'w') as arquivo:
        json.dump(dis_to_save, arquivo, indent=4)


# PRE GAME
def game_information(players
                     , buyin
                     , fichas
                     , save=True
                     , inputed_game=False):
    """
    Gera as informações do jogo e opcionalmente persiste no Firestore.
    """
    dis_jogo = {
        "id_jogo": str(uuid.uuid4()),
        "players": players,
        "buyin": buyin,
        "fichas": fichas,
        "unitario": buyin / fichas,
        "start": dt.datetime.now().strftime("%H:%M:%S"),
        "data": str(dt.date.today()),
    }
    if "game" not in st.session_state:
        st.session_state["game"] = dis_jogo
    elif 'game' in st.session_state and st.session_state["game"] == {}:
        st.session_state["game"] = dis_jogo
    if not inputed_game:
        st.session_state["status"] = "in"
    if save:
        save_game_state()




def game_status():
    load_game_state()
    if "status" not in st.session_state:
        st.session_state["status"] = "pre"


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
    start = dt.datetime.strptime(st.session_state["game"]["start"], "%H:%M:%S")
    if "time_played" not in st.session_state:
        st.session_state["time_played"] = {x: None for x in st.session_state["game"]["players"]}
    changes = st.session_state.get("in_game_changes") or {}
    for k, v in changes.get("edited_rows", {}).items():
        playa = st.session_state["game_data"].loc[int(k), "Players"]
        if "Final" in v.keys() and st.session_state["time_played"][playa] is None:
            f = dt.datetime.now()
            match_time = f - start
            st.session_state["time_played"][playa] = str(match_time).split(",")[1].split(".")[0]


def on_in_game_data_change():
    """Callback do data_editor: atualiza tempo jogado e persiste o estado."""
    time_played()
    save_game_state()


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
        if fichas_totais > fichas_finais:
            return f"""Fichas finais informadas não batem com as jogadas
            \nFichas faltantes: {fichas_totais-fichas_finais:.0f}""", True
        elif fichas_totais < fichas_finais:
            return f"""Fichas finais informadas não batem com as jogadas
            \nFichas a mais: {fichas_finais-fichas_totais:.0f}""", True
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
        # st.image(r"images\unknown.jpg",
        #          caption="1° Lugar")
        st.title("A imagem não carregou porra")


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

    ## AQUI VAI PRECISAR RECEBER O NOME DO JOGO
    
    data = st.session_state[f'game']['data']
    participantes = len(st.session_state[f'game']['players'])
    id_jogo = st.session_state[f'game']['id_jogo']
    nome_jogo = st.session_state['nome_jogo']

    tabela_jogo = pd.DataFrame({"id_jogo":id_jogo
                                , 'nome_jogo': nome_jogo
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
    
    print("\n\n\n")
    print(join_tables(dia).reset_index())
    print("\n\n\n")
    df_playa = join_tables(dia).reset_index()
    df_playa.columns = ['player', 'rebuys', 'stack_final', 'pago', 'ganho', 'saldo', 'tempo_jogo']
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

    games = pd.concat(games, axis=0, ignore_index=True)
    players = pd.concat(players, axis=0, ignore_index=True)

    return games, players
