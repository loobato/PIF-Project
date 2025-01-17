import json
import numpy as np
import pandas as pd
import streamlit as st
import auxiliares as aux
import datetime as dt
from end_game_page import end_game


def in_game():
    dia = dt.date.today().strftime("%d/%m/%y")
    comeco = st.session_state[f'game_{dia}']['start']
    buyin = st.session_state[f'game_{dia}']['buyin']
    stack = st.session_state[f'game_{dia}']['fichas']
    unitario = buyin / stack

    df_game_session = pd.DataFrame({"Players":st.session_state[f'game_{dia}']['players']
                                    , "BI Pg":[False for i in range(len(st.session_state[f'game_{dia}']['players']))] 
                                    , f"Rebuys":[0 for i in range(len(st.session_state[f'game_{dia}']['players']))]
                                    , "RB Pg":[False for i in range(len(st.session_state[f'game_{dia}']['players']))]
                                    , "Final":[None for i in range(len(st.session_state[f'game_{dia}']['players']))]
                                    })
    st.header(f":material/poker_chip: PIF Millions {st.session_state[f'game_{dia}']['fichas']}k :material/poker_chip:")
    
    overview = st.container()

    with overview:
        col1_ovr, col2_ovr = st.columns([35, 65], border=True)

        st.markdown("""
                    <style>
                    [data-testid=stColumn]:nth-of-type(1) [data-testid=stVerticalBlock]{
                        gap: 0rem;
                    }
                    </style>
                    """,unsafe_allow_html=True)
        
        with col2_ovr:
            if 'game data' not in st.session_state:
                st.session_state['game_data'] = st.data_editor(df_game_session,
                                                                column_config={
                                                                    "BI Pg":st.column_config.CheckboxColumn()
                                                                    , "RB Pg":st.column_config.CheckboxColumn()
                                                                    , "Rebuys":st.column_config.NumberColumn(step=1)
                                                                    , "Final":st.column_config.NumberColumn()
                                                                }
                                                                , hide_index=True
                                                                , key='in_game_changes'
                                                                , on_change=aux.time_played)
                
        with col1_ovr:

            
            aux.game_timer(comeco, dia)
            st.caption(f"{dia} | {comeco}")
            st.empty()
            col1, col2 = st.columns(2)
            
            with col1:
                st.caption(f'*Stack inicial*')
                st.caption(f'*Buy-In*')
                st.caption(f'*Valor unitário*')
        
            with col2:
                st.caption(f'**{stack} fichas**')
                st.caption(f'**R$ {buyin}**')
                st.caption(f'**R$ {unitario:.2f}**')

            st.divider()

            with st.popover("End Game?", icon=":material/check_circle:"):
                texto, disabilitar = aux.trava_end(dia)
                st.warning(texto)
                
                col1_pop, col2_pop = st.columns(2)
                with col1_pop:
                    pass
                    # stop_watch = st.button("Parar relógio", key="stop_watch")


                with col2_pop:
                    butao = st.button("End Game", disabled=disabilitar, key='end_button')

                if butao:
                    st.session_state['status'] = 'end'

                                    