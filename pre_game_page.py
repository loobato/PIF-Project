import json
import numpy as np
import pandas as pd
import streamlit as st
import auxiliares as aux

def pre_game():

    col_part, col_gamemode = st.columns([0.4, 0.6])

    with col_part:
        st.markdown(":material/group_add: Participantes")
        p = aux.read_json('pif_info.json')
        lis_participantes = list(p['participantes'].keys())
        df_participantes = pd.DataFrame({'Participantes':sorted(lis_participantes),
                                        "Jogando":[False for i in range(len(lis_participantes))]})

        jogadores = st.data_editor(df_participantes
                    , column_config={
                        "jogando": st.column_config.CheckboxColumn(
                            default=False
                        )
                    }
                    , hide_index=True
                    , num_rows='dynamic')
        
        online = jogadores.loc[jogadores['Jogando'] == True].Participantes.values

    with col_gamemode:
        st.markdown(":material/manufacturing: Configurações do Jogo")
        # with st.form('gamemode'):
            
        buy_in = st.number_input("Buy In"
                                , value=20
                                )
        fichas = st.number_input("Fichas iniciais"
                                 , value=1500
                                , step=100
                                )


        if len(online) < 2:
            st.button("Jogar", disabled=True)
            st.caption("Selecione no mínimo 2 jogadores")
        else:
            st.button("Jogar"
                                , disabled=False
                                , on_click=aux.game_information
                                , args=(online, buy_in, fichas))
            st.caption(f"{len(online)} jogadores")
        