import json
import numpy as np
import pandas as pd
import streamlit as st
import auxiliares as aux
from pre_game_page import pre_game
from in_game_page import in_game
from end_game_page import end_game

aux.game_status()

if st.session_state["status"] == 'pre':
    pre_game()
    
elif st.session_state["status"] == 'in':
    in_game()

elif st.session_state["status"] == 'end':
    end_game()

with st.expander("state"):
    st.write(st.session_state)