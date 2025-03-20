import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO

st.title("📊 Dashboard Previdenciário Simplificado")

# Entrada de dados
st.header("📥 Inserção dos Dados")
file = st.file_uploader("Upload CNIS ou Carta (CSV/XLS)", type=['csv', 'xls', 'xlsx'])
data_txt = st.text_area("Ou cole os dados em formato texto")

def load_data(uploaded_file, txt_data):
    if uploaded_file:
        if uploaded_file.name.endswith('csv'):
            return pd.read_csv(uploaded_file)
        else:
            return pd.read_excel(uploaded_file)
    elif txt_data:
        try:
            return pd.read_csv(StringIO(txt_data), sep=None, engine='python')
        except:
            return None
    return None

df = load_data(file, data_txt)

if df is not None:
    st.subheader("🔎 Dados Carregados")
    st.dataframe(df)

    st.header("🧮 Cálculo Previdenciário")
    df_sorted = df.sort_values(by=df.columns[0])
    df_top = df_sorted.nlargest(int(0.8 * len(df_sorted)), df.columns[1])
    media = df_top[df.columns[1]].mean()

    Tc = 38 + (1/12) + (25/365)
    a = 0.31
    Es = 21.8
    Id = 60
    FP = (Tc * a / Es) * (1 + ((Id + Tc * a) / 100))
    beneficio = media * FP

    st.write(f"**Média dos 80% maiores salários:** R$ {media:,.2f}")
    st.write(f"**Fator Previdenciário:** {FP:.4f}")
    st.write(f"**Salário de Benefício:** R$ {beneficio:,.2f}")

    st.subheader("📅 Normativa Aplicada")
    df['Normativa'] = ["Lei 8.213/91" if int(str(x)[:4]) < 2019 else "Pós-2019" for x in df[df.columns[0]]]
    st.dataframe(df[[df.columns[0], df.columns[1], 'Normativa']])

    st.subheader("📈 Gráfico dos Salários (Top 80%)")
    plt.figure(figsize=(10,4))
    plt.bar(df_top[df.columns[0]], df_top[df.columns[1]])
    plt.xticks(rotation=45)
    plt.ylabel("Remuneração")
    st.pyplot(plt)

    st.download_button("📥 Exportar Resultado (CSV)", data=df.to_csv(index=False), file_name='resultado_simplificado.csv')

    st.markdown("---")
    st.info("Cálculo realizado conforme Lei 8.213/91 e Instruções Normativas vigentes. Pronto para revisão judicial.")
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
