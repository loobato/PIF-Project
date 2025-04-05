import json
import numpy as np
import pandas as pd
import streamlit as st
import auxiliares as aux
from pre_game_page import pre_game
from in_game_page import in_game
from end_game_page import end_game

st.set_page_config("PIF App v1", page_icon="🃏")

st.image("https://raw.githubusercontent.com/loobato/PIF-Project/refs/heads/main/images/ISA%20(1).png")

# st.title("Poker Isa Formou App")
st.markdown("*Um aplicativo feito em parceria pela CASA em collab com Mark Zuckerberg*")

pg = st.navigation([
    st.Page("game_screen.py", title="Game Screen")
    , st.Page("scoreboard.py", title="Scoreboard")
])

pg.run()