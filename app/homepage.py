import json
import sys
from pathlib import Path

# Ensure project root is on path so 'support' resolves when running streamlit run app/homepage.py
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import numpy as np
import pandas as pd
import streamlit as st
import support.auxiliares as aux
from support.gcp_config import Database
from game.pre_game_page import pre_game
from game.in_game_page import in_game
from game.end_game_page import end_game

st.set_page_config("PIF App v1", page_icon="🃏")

st.image("https://raw.githubusercontent.com/loobato/PIF-Project/refs/heads/main/images/ISA%20(1).png")

# st.title("Poker Isa Formou App")
st.markdown("*Um aplicativo feito em parceria pela CASA em collab com Mark Zuckerberg*")

if "db" not in st.session_state:
    st.session_state["db"] = Database(default_client="firebase")

pg = st.navigation([
    st.Page(r"game/game_screen.py", title="Game Screen")
    , st.Page(r"scoreboard/scoreboard.py", title="Scoreboard")
    # , st.Page(r"game/input_game_scores.py", title="Inputar Jogo")
])

pg.run()