import json
import numpy as np
import pandas as pd
import streamlit as st
import support.auxiliares as aux
import datetime as dt


def end_game():
    dia = dt.date.today().strftime("%d/%m/%y")
    comeco = st.session_state[f'game']['start']
    fim = st.session_state[f'game']['finish']
    tempo = st.session_state[f'game']['duration']
    buyin = st.session_state[f'game']['buyin']
    fichas_iniciais = st.session_state[f'game']['fichas']
    unitario = buyin / fichas_iniciais 
    

    st.title('Resultados da Pelada')
    tabela_saldos = aux.game_saldos(dia)


    game_overview, podium = st.columns([50, 60], gap='medium')

    with game_overview:
        with st.container():

            st.text_input(
                "nome_do_jogo"
                , value=f"PIF Millions {st.session_state[f'game']['fichas']}k - {dia}"
                , key='nome_jogo'
                , label_visibility='hidden')

            st.button("Salvar nome do jogo"
                        , key='save_game_name'
                        , disabled=True # ARRUMAR O UPDATE E TIRAR ISSO
                        )

            if st.session_state['save_game_name']:                
                aux.update_game_name(
                    st.session_state['game']['id_jogo']
                    , st.session_state['nome_jogo']
                    )                
                st.session_state['save_game_name'] = False
            
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
                st.caption(f'**R$ {round(unitario, 3)}**')

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

    #######################################
    game_data = aux.game_table(dia, comeco, fim, tempo, buyin, fichas_iniciais)
    playa_data = aux.playa_table(dia)

    # st.write(game_data)
    # st.write(playa_data)

    # SALVA O JOGO NO BIGQUERY (games_table + players_table) e marca jogo finalizado no Firestore
    
    if 'saved_to_bq' not in st.session_state:
        st.session_state['saved_to_bq'] = False
        aux.save_game_to_firestore(str(st.session_state['nome_jogo']), game_data, playa_data)

    # EXPANDER DOS RESULTADOS DO JOGO
    with st.expander("Resultados do Jogo"):
        st.dataframe(aux.join_tables(dia)
                     , column_config={
                         'Á Pagar':st.column_config.NumberColumn(format="R$ %.2f")
                         , 'Á Receber':st.column_config.NumberColumn(format="R$ %.2f")
                         , 'Saldo':st.column_config.NumberColumn(format="R$ %.2f")
                     })
        
        save = st.button("Salvar resultados")

    if save:
        path_game = f"saves\game_{dia.replace('/', '')}.csv"
        path_playa = f"saves\playa_{dia.replace('/', '')}.csv"
        aux.game_table(dia, comeco, fim, tempo, buyin, fichas_iniciais).to_csv(path_game)
        aux.playa_table(dia).to_csv(path_playa)
    
    botao = st.button("Voltar a tela inicial")
    if botao:
        st.session_state["status"] = "pre"
        st.session_state['game'] = {}
        