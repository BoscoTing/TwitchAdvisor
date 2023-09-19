import streamlit as st
import pandas as pd
import numpy as np
import time

from stats import execute_query

df_active = pd.DataFrame(columns=["messages", "chatters", "calculated_at"]).set_index("calculated_at") 
chart_data = execute_query(df_active)