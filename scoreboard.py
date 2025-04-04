import pandas as pd
import streamlit as st
import auxiliares as aux

st.title("Scoreboard P.I.F")

games, jogadores = aux.read_tables()

jogadores.tempo_jogo = pd.to_timedelta(jogadores.tempo_jogo)
# fazer contagem de jogos por jogador

tab_games, tab_players = st.tabs(["Jogos", "Jogadores"])

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
        ))

with tab_players:
    st.dataframe(jogadores.groupby("player").sum()
                 , column_config={
                     "player": st.column_config.TextColumn("Jogador")
                     , "tempo_jogo": st.column_config.NumberColumn("Tempo de Jogo")
                     , "stack_final": st.column_config.NumberColumn("Stack Total")
                     , "rebuys": st.column_config.NumberColumn("Rebuys")
                     , "pago": st.column_config.NumberColumn("Pago", format="R$ %.2f")
                     , "ganho": st.column_config.NumberColumn("Ganho", format="R$ %.2f")
                     , "saldo": st.column_config.NumberColumn("Saldo", format="R$ %.2f")
                 }
                 , column_order=(
                     "player"
                     , "tempo_jogo"
                     , "stack_final"
                     , "rebuys"
                     , "pago"
                     , "ganho"
                     , "saldo"
                 ))