import json
import numpy as np
import pandas as pd
import streamlit as st
import auxiliares as aux
from pre_game_page import pre_game
from in_game_page import in_game
from end_game_page import end_game

st.set_page_config("PIF App v1", page_icon="🃏")

st.image(r"images\ISA (1).png")

# st.title("Poker Isa Formou App")
st.markdown("*Um aplicativo feito em parceria pela CASA em collab com Mark Zuckerberg*")

aux.game_status()

if st.session_state["status"] == 'pre':
    pre_game()
    
elif st.session_state["status"] == 'in':
    in_game()

elif st.session_state["status"] == 'end':
    end_game()

with st.expander("state"):
    st.write(st.session_state)