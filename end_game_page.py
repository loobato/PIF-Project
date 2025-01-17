import json
import numpy as np
import pandas as pd
import streamlit as st
import auxiliares as aux
import datetime as dt


def end_game():
    dia = dt.date.today().strftime("%d/%m/%y")
    comeco = st.session_state[f'game_{dia}']['start']
    fim = st.session_state[f'game_{dia}']['finish']
    tempo = st.session_state[f'game_{dia}']['duration']
    buyin = st.session_state[f'game_{dia}']['buyin']
    fichas_iniciais = st.session_state[f'game_{dia}']['fichas']
    unitario = buyin / fichas_iniciais 
    
    st.title('Resultados da Pelada')
    st.markdown(f"*PIF Millions {st.session_state[f'game_{dia}']['fichas']}k - {dia}*")
    tabela_saldos = aux.game_saldos(dia)

    game_overview, podium = st.columns([50, 60], gap='medium')

    with game_overview:
        with st.container():

            st.markdown("""
                        <style>
                        [data-testid=stColumn]:nth-of-type(1) [data-testid=stVerticalBlock]{
                            gap: 0rem;
                        }
                        </style>
                        """,unsafe_allow_html=True)

        
            st.title(tempo)
            st.caption(f"{dia} | {comeco} | {fim}")

            col1, col2 = st.columns(2)
            with col1:
                st.caption(f'*Stack inicial*')
                st.caption(f'*Buy-In*')
                st.caption(f'*Valor unitário*')
        
            with col2:
                st.caption(f'**{fichas_iniciais} fichas**')
                st.caption(f'**R$ {buyin}**')
                st.caption(f'**R$ {unitario:.2f}**')

        st.divider()
    
        st.dataframe(tabela_saldos.sort_values(by='Saldo', ascending=False)
                        , column_config={
                            "Pagar":st.column_config.NumberColumn(format="R$ %f")
                            , "Receber":st.column_config.NumberColumn(format="R$ %.2f")
                            , "Saldo":st.column_config.NumberColumn(format="R$ %.2f")
                        })
            
    with podium:
        pod = tabela_saldos.sort_values(by='Saldo', ascending=False).head(3).index.values

        aux.results(pod)
        st.balloons()
    
    with st.expander("Resultados do Jogo"):
        st.dataframe(aux.join_tables(dia)
                     , column_config={
                         'Á Pagar':st.column_config.NumberColumn(format="R$ %.2f")
                         , 'Á Receber':st.column_config.NumberColumn(format="R$ %.2f")
                         , 'Saldo':st.column_config.NumberColumn(format="R$ %.2f")
                     })
        
        save = st.button("Salvar resultados")

    if save:
        path_game = f"saves\game_{dia.replace('/', '')}"
        path_playa = f"saves\playa_{dia.replace('/', '')}"
        aux.game_table(dia, comeco, fim, tempo, buyin, fichas_iniciais).to_csv(path_game)
        aux.playa_table(dia).to_csv(path_playa)
        