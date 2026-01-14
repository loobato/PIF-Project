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

        col1, col2 = st.columns(2)

        
        with col1:
            if len(online) < 2:
                st.button("Jogar"
                          , disabled=True
                          , help="Selecione no mínimo 2 jogadores")
            else:
                st.button("Jogar"
                        , disabled=False
                        , on_click=aux.game_information
                        , args=(online, buy_in, fichas))
                st.caption(f"{len(online)} jogadores")
        
        with col2:

            if len(online) < 2:
                igs = st.button("Inputar Jogo"
                                , disabled=True
                                , help="Selecione no mínimo 2 jogadores")
            else:
                igs = st.button("Inputar Jogo"
                                , disabled=False)
                
                if 'igs' not in st.session_state:
                    st.session_state['igs'] = False
                if igs:
                    st.session_state['igs'] = True

                

    if 'igs' in st.session_state and st.session_state['igs']:
        # fazer funcao disso
        import datetime as dt
        aux.game_information(online
                             , buy_in
                             , fichas
                             , save=False
                             , inputed_game=True)
        dia = dt.date.today().strftime("%d/%m/%y")
        comeco = st.session_state[f'game']['start']
        buyin = st.session_state[f'game']['buyin']
        fichas_iniciais = st.session_state[f'game']['fichas']
        unitario = buyin / fichas_iniciais 

        df_scores = pd.DataFrame(
            index=online
            , columns=[
                'Rebuys'
                , "Pago"
                 , 'Fichas Finais'
                 , "Á Pagar"
                 , 'Á Receber'
                 , 'Saldo'
                 , 'Tempo de Jogo'
                ]
        )
        df_scores = df_scores.fillna(0)

        data = st.date_input("Data"
                             , value=dt.datetime.today()
                             , format="DD/MM/YYYY")
        _col1, _col2 = st.columns(2)
        
        with _col1:
            hora_inicio = st.time_input("Começou:")
        with _col2:
            hora_fim = st.time_input("Terminou")

        # dt.datetime.combine(data)
        
        if hora_fim < hora_inicio:
            data_fim = data + dt.timedelta(1)
        else: 
            data_fim = data
        
        inicio = dt.datetime.combine(data, hora_inicio)
        fim = dt.datetime.combine(data_fim, hora_fim)
        diff = fim-inicio
        total = int(diff.seconds)
        horas, resto = divmod(total, 3600)
        minutos, segundos = divmod(resto, 60)

        tempo_str = f"{horas:02}:{minutos:02}:{segundos:02}"
        st.session_state[f'game']['duration'] = tempo_str
        st.write(tempo_str)
        tempos_iniciais = [tempo_str for i in range(len(online))]
    
        df_scores['Tempo de Jogo'] = tempos_iniciais


        inputes = st.data_editor(df_scores)
        
        save = st.button("Salvar resultados")

        if save:
            # fazer função
            data = data.strftime("%Y-%M-%d")
            path_game = rf"saves\game_{dia.replace('/', '')}"
            path_game = rf"saves\teste.csv"                         # TIRAR ISSO
            path_playa = rf"saves\playa_{dia.replace('/', '')}"
            path_playa = rf"saves\teste2.csv"                       # TIRAR ISSO

            id_jogo = ''.join(data.split('-'))+f'-{len(online)}'

            tabela_jogo = pd.DataFrame({"id_jogo": id_jogo
                                , "data_jogo":data
                                , "participantes":len(online)
                                , "inicio":comeco
                                , "fim":fim
                                , "tempo":tempo_str
                                , "buyin":buyin
                                , "stack_inicial":fichas_iniciais
                                }
                                , index=[0])
            st.dataframe(tabela_jogo)
            tabela_jogo.to_csv(path_game)

            # ESSAS COLUNAS PRECISAM CONSTAR PARA FAZER O SAVE[]
            df_playa = inputes.copy()
            df_playa = df_playa.reset_index()
            df_playa.columns = [
                'player'
                , 'rebuys'
                , 'pago'
                , 'stack_final'
                , 'apagar'
                , 'ganho'
                , 'saldo'
                , 'tempo_jogo'
            ]

            df_playa['id_jogo'] = [id_jogo for i in range(len(df_playa.index))]
            
            df_playa['id_player'] = [aux.read_json('pif_info.json')['participantes'][x]['id']
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
            st.dataframe(df_playa)
            tabela_jogo.to_csv(path_game)



            # aux.game_table(dia, comeco, fim, tempo_str, buyin, fichas_iniciais).to_csv(path_game)
            # aux.playa_table(dia).to_csv(path_playa)
            # automatizar calculos
