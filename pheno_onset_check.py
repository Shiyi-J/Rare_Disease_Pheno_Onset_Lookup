import streamlit as st
from pathlib import Path
import pickle
import pandas as pd
import numpy as np

# ==================================================
# PAGE CONFIGURATION
# ==================================================
st.set_page_config(
    page_title='Phenotype Onset Lookup for Rare Diseases', page_icon="🔎", layout="wide")

# ==================================================
# CUSTOM CSS
# ==================================================
st.markdown("""
    <style>
    .main-title {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 5px;
    }
    .subtitle {
        font-size: 18px;
        color: #666666;
        margin-bottom: 25px;
    }
    </style>
    """, unsafe_allow_html=True)

# ==================================================
# TITLE
# ==================================================
st.markdown('<div class="main-title">Phenotype Onset Lookup for Rare Diseases</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">'
    'Search the knowledgebase and select a rare disease to view its related phenotype onset.'
    '</div>', unsafe_allow_html=True)
st.divider()

# ==================================================
# DATA LOCATION
# ==================================================
# name id conversion
df_ref = pd.read_json('name_conversion_table.json', orient='records')

data_folder = Path('onset_stats')
json_files = data_folder.glob('*_onset_days_sum.json')
# Create dictionary:
# {"Apple": Path("data/Apple.json"),
#  "Banana": Path("data/Banana.json"), ...}
options = dict()
for file in json_files:
    name_id = int(file.stem.split('_')[0])
    name_str = df_ref[df_ref['concept_id']==name_id]['concept_name'].iloc[0]
    name_code = df_ref[df_ref['concept_id']==name_id]['concept_code'].iloc[0]
    name_concat = name_str + ' '*10 + name_code
    options[name_concat] = file
option_names = list(options.keys())

# ==================================================
# SEARCH
# ==================================================
search = st.text_input("🔎 Search", placeholder="Type a rare disease name here...")
# Filter options
if search:
    filtered_options = [option for option in option_names if search.lower() in option.lower()]
else:
    filtered_options = option_names

# decide what to display
if search and not filtered_options:
    st.warning(f'"{search}" has not yet been included in the database.')
else:
    if search:
        st.write(f"**{len(filtered_options)} option(s) found**")
    selected_option = st.selectbox("Select an option:", filtered_options, index=None, placeholder="Choose an option...")

    # ==================================================
    # DISPLAY SELECTED DATA
    # ==================================================
    if selected_option:
        selected_file = options[selected_option]
        try:
            df_raw = pd.read_json(selected_file, orient='records')
            # filter terms
            name = df_ref[df_ref['concept_code']==selected_option.split(' ')[-1]]['concept_id'].iloc[0]
            with open('association_holm/'+str(name)+'_pheno.pkl', 'rb') as f:
                pheno_list = pickle.load(f)
            df_raw = df_raw[df_raw['HPO_id'].isin(pheno_list)]
            # proceed
            df_raw = df_raw.loc[df_raw['show_online'], ['HPO_id', 'aggregated_median', 'aggregated_q1', 'aggregated_q3']]
            df_raw['Median Onset Age'] = np.round(df_raw['aggregated_median'] / 365, 1)
            df_raw['Q1 Onset Age'] = np.round(df_raw['aggregated_q1'] / 365, 1)
            df_raw['Q3 Onset Age'] = np.round(df_raw['aggregated_q3'] / 365, 1)
            df_raw['Interquartile Range of Onset Age'] = df_raw['Q1 Onset Age'].astype(str) + ' - ' + df_raw['Q3 Onset Age'].astype(str)
            df_raw = df_raw[['HPO_id', 'Median Onset Age', 'Interquartile Range of Onset Age']]
            df_merge = df_raw.merge(df_ref, how='left', left_on='HPO_id', right_on='concept_code')
            df = df_merge[['concept_name', 'HPO_id', 'Median Onset Age', 'Interquartile Range of Onset Age']].copy()
            df = df.rename(columns={'concept_name':'Phenotype Name', 'HPO_id':'HPO Identifier'})

            st.divider()
            st.subheader(selected_option)
            st.dataframe(df, width='stretch', hide_index=True)
        except Exception as e:
            st.error(f"Unable to read {selected_file.name}: {e}")
