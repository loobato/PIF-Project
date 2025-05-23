import pandas as pd
import streamlit as st
import auxiliares as aux

st.title("Scoreboard P.I.F")

games, jogadores = aux.read_tables()

games = games.sort_values("data_jogo",ascending=True, ignore_index=True)

jogadores.tempo_jogo = pd.to_timedelta(jogadores.tempo_jogo)
qtde_jogos = jogadores.player.value_counts()
tabela_jogador = jogadores.groupby("player").sum()
tabela_jogador['qtd_jogo'] = qtde_jogos
# fazer contagem de jogos por jogador

tab_games, tab_players, tab_detail_game = st.tabs(["Jogos", "Jogadores", "Por Jogo"])

with tab_games:
    st.dataframe(
        games
        , column_config={
            "data_jogo": st.column_config.DateColumn("Data", format="DD/MM/YY")
            , "participantes": st.column_config.NumberColumn("Participantes")
            , "inicio": st.column_config.TextColumn("Começo (h)", width="small")
            , "fim": st.column_config.TextColumn("Fim (h)", width="small")
            , "tempo": st.column_config.TextColumn("Duração (h)", width="small")
            , "buyin": st.column_config.NumberColumn("Buy-In", format="R$ %.2f", width="small")
            , "stack_inicial": st.column_config.NumberColumn("Stack Inicial")
        },
        column_order=(
            "data_jogo"
            , "participantes"
            , "inicio"
            , "fim"
            , "tempo"
            , "buyin"
            , "stack_inicial"
        ),
        hide_index=True)

with tab_players:
    st.dataframe(tabela_jogador
                 , column_config={
                     "player": st.column_config.TextColumn("Jogador", width="small")
                     , "qtd_jogo": st.column_config.NumberColumn("Qnt. Jogos", width="small")
                     , "tempo_jogo": st.column_config.NumberColumn("Tempo de Jogo")
                     , "stack_final": st.column_config.NumberColumn("Stack Total")
                     , "rebuys": st.column_config.NumberColumn("Rebuys")
                     , "pago": st.column_config.NumberColumn("Pago", format="R$ %.2f")
                     , "ganho": st.column_config.NumberColumn("Ganho", format="R$ %.2f")
                     , "saldo": st.column_config.NumberColumn("Saldo", format="R$ %.2f")
                 }
                 , column_order=(
                     "player"
                     , "qtd_jogo"
                     , "tempo_jogo"
                     , "stack_final"
                     , "rebuys"
                     , "pago"
                     , "ganho"
                     , "saldo"
                 ))
    
with tab_detail_game:
    for i in range(games.shape[0]):
        col1, col2 = st.columns(2)
        data = pd.to_datetime(games.loc[i, "data_jogo"])
        buyin = games.loc[i, "buyin"]
        stack = games.loc[i, "stack_inicial"]
        duracao = games.loc[i, "tempo"]
        id = games.loc[i, "id_jogo"]
        players_pelada = jogadores[jogadores["id_jogo"] == id].sort_values("saldo", ascending=False)
        players_pelada.index = [i for i in range(1, players_pelada.shape[0]+1)]
        
        with col1:
            st.caption(f'{data.strftime("%d/%m/%Y")} | {duracao}')
        with col2:
            st.caption(f'R$ {buyin} | {stack} fichas')
        
        st.dataframe(players_pelada
                     , column_config={
                     "player": st.column_config.TextColumn("Jogador", width="small")
                     , "qtd_jogo": st.column_config.NumberColumn("Qnt. Jogos", width="small")
                     , "tempo_jogo": st.column_config.NumberColumn("Tempo de Jogo")
                     , "stack_final": st.column_config.NumberColumn("Stack Total")
                     , "rebuys": st.column_config.NumberColumn("Rebuys")
                     , "pago": st.column_config.NumberColumn("Pago", format="R$ %.2f")
                     , "ganho": st.column_config.NumberColumn("Ganho", format="R$ %.2f")
                     , "saldo": st.column_config.NumberColumn("Saldo", format="R$ %.2f")
                     }
                     , column_order=(
                         "player"
                         , "qtd_jogo"
                         , "tempo_jogo"
                         , "stack_final"
                         , "rebuys"
                         , "pago"
                         , "ganho"
                         , "saldo"
                     ))

