import streamlit as st
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import gspread
from google.oauth2.service_account import Credentials

# ========================
# 1. Conectar ao Google Sheets
# ========================
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file('credenciais.json', scopes=SCOPES)
client = gspread.authorize(creds)

# Abrir a planilha pelo link
sheet_url = 'https://docs.google.com/spreadsheets/d/1nWNE9KB7o1I8lgqY-V29pSXjNNmwpq57vyz_14FfTC0/edit?usp=sharing'
spreadsheet = client.open_by_url(sheet_url)
sheet = spreadsheet.sheet1

data = sheet.get_all_records()
df = pd.DataFrame(data)

# ========================
# 2. Decoupagem dos Campos
# ========================
df['Ano'] = df['Nome'].str.extract(r'(\d{4})')
df['Municipio'] = df['Nome'].str.extract(r'(BENEDITO LEITE|\b[A-Z ]+\b)')
df['Artefato'] = df['Subclasse_Funcional']

# ========================
# 3. Início do Streamlit
# ========================
st.set_page_config(page_title='Dashboard Documental', layout='wide')
st.title('📊 Dashboard Documental - Lógica Fuzzy')

# ========================
# 4. Filtros Dinâmicos
# ========================
col1, col2, col3 = st.columns(3)
with col1:
    ano_filter = st.multiselect('Selecione o Ano:', options=sorted(df['Ano'].dropna().unique()), default=sorted(df['Ano'].dropna().unique()))
with col2:
    municipio_filter = st.multiselect('Selecione o Município:', options=df['Municipio'].dropna().unique(), default=df['Municipio'].dropna().unique())
with col3:
    classe_filter = st.multiselect('Selecione a Classe:', options=df['Classe_Final_V2'].unique(), default=df['Classe_Final_V2'].unique())

# Aplicar filtros
filtered_df = df[
    (df['Ano'].isin(ano_filter)) &
    (df['Municipio'].isin(municipio_filter)) &
    (df['Classe_Final_V2'].isin(classe_filter))
]

# ========================
# 5. Tabs do Dashboard
# ========================
tab1, tab2, tab3 = st.tabs(['📈 Representação Gráfica', '📑 Estatísticas', '🧩 Artefatos e Nuvem'])

# ========================
# 6. Representação Gráfica
# ========================
with tab1:
    st.subheader('Distribuição de Artefatos por Ano')
    fig1 = px.histogram(filtered_df, x='Ano', color='Classe_Final_V2', barmode='group')
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader('Distribuição por Classe')
    fig2 = px.pie(filtered_df, names='Classe_Final_V2', title='Proporção por Classe')
    st.plotly_chart(fig2, use_container_width=True)

# ========================
# 7. Estatísticas
# ========================
with tab2:
    st.subheader('Resumo Estatístico')
    count_table = filtered_df.groupby(['Ano', 'Classe_Final_V2']).size().reset_index(name='Contagem')
    st.dataframe(count_table)

# ========================
# 8. Artefatos e Nuvem de Palavras
# ========================
with tab3:
    st.subheader('Artefatos por Termo Detectado')
    st.dataframe(filtered_df[['Nome', 'Termo Detectado', 'Link']].dropna())

    st.subheader('Nuvem de Palavras - Termos Detectados')
    terms = ' '.join(filtered_df['Termo Detectado'].dropna().astype(str).tolist())
    if terms:
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(terms)
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        st.pyplot(plt)
    else:
        st.write('Nenhum termo detectado para exibir.')

# ========================
# 9. Footer
# ========================
st.caption('Construído com Streamlit + Integração Google Sheets | Publicação GitHub + Streamlit Cloud')
