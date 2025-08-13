import streamlit as st
import pandas as pd
import spacy
from spacy.language import Language

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA E DO MODELO DE IA
# -----------------------------------------------------------------------------

st.set_page_config(page_title="Anonimizador de Notas de Alta", layout="wide")

@st.cache_resource
def carregar_modelo_spacy() -> Language:
    st.write("Carregando modelo de linguagem (spaCy)... Isso pode levar alguns segundos.")
    modelo = spacy.load('pt_core_news_lg')
    st.write("✅ Modelo carregado com sucesso!")
    return modelo

@st.cache_data
def carregar_dados_locais(caminho_arquivo: str) -> pd.DataFrame:
    """
    Carrega o arquivo de dados .pkl do repositório.
    Usa o cache para evitar recarregamentos desnecessários.
    """
    try:
        df = pd.read_pickle(caminho_arquivo)
        return df
    except FileNotFoundError:
        st.error(f"Erro: O arquivo de dados '{caminho_arquivo}' não foi encontrado no repositório do GitHub. Certifique-se de que o nome está correto e que o arquivo foi enviado.")
        return None

# Carrega o modelo de IA
nlp = carregar_modelo_spacy()

# Carrega o DataFrame do arquivo local
df = carregar_dados_locais("Data_LLMs_and_Gold_and_EHRs.pkl")

# -----------------------------------------------------------------------------
# FUNÇÃO DE ANONIMIZAÇÃO (mesma de antes)
# -----------------------------------------------------------------------------

def anonimizar_texto(texto: str) -> str:
    if not isinstance(texto, str) or texto.strip() == "":
        return texto
    doc = nlp(texto)
    texto_anonimizado = texto
    for entidade in reversed(doc.ents):
        if entidade.label_ in ['PER', 'LOC']:
            texto_anonimizado = texto_anonimizado[:entidade.start_char] + f'[{entidade.label_}]' + texto_anonimizado[entidade.end_char:]
    return texto_anonimizado

# -----------------------------------------------------------------------------
# INTERFACE DA APLICAÇÃO STREAMLIT
# -----------------------------------------------------------------------------

st.title("FERRAMENTA DE ANONIMIZAÇÃO DE NOTAS DE ALTA 🩺")
st.markdown("""
Esta ferramenta utiliza Inteligência Artificial para identificar e remover **nomes de pessoas (PER)** e **locais (LOC)** de textos.
O DataFrame `Data_LLMs_and_Gold_and_EHRs.pkl` foi carregado diretamente do repositório.

**Instruções:**
1.  Selecione a coluna que contém o texto a ser anonimizado.
2.  Clique no botão para iniciar o processo.
3.  Revise o resultado e faça o download do arquivo modificado.

⚠️ **Atenção:** A anonimização automática não é perfeita. **É fundamental que um humano revise o resultado final.**
""")

# Só continua se o DataFrame foi carregado com sucesso
if df is not None:
    st.success(f"Arquivo 'Data_LLMs_and_Gold_and_EHRs.pkl' carregado com sucesso! ({len(df)} linhas)")
    
    colunas = df.columns.tolist()
    try:
        default_index = colunas.index("25. Evolução Alta") # Tenta encontrar a coluna padrão
    except ValueError:
        default_index = 0
        
    coluna_selecionada = st.selectbox(
        "1. Selecione a coluna com o texto para anonimizar:",
        colunas,
        index=default_index
    )
    
    st.write("Amostra da coluna selecionada:")
    st.dataframe(df[[coluna_selecionada]].head())

    if st.button("🚀 Iniciar Anonimização", type="primary"):
        nova_coluna_nome = f"anonimizado_{coluna_selecionada}"
        with st.spinner(f"Anonimizando {len(df)} linhas..."):
            df[nova_coluna_nome] = df[coluna_selecionada].apply(anonimizar_texto)
        
        st.success("Processo de anonimização concluído!")
        st.write("Amostra do resultado:")
        st.dataframe(df[[coluna_selecionada, nova_coluna_nome]].head())
        
        @st.cache_data
        def converter_df_para_csv(dataframe):
            return dataframe.to_csv(index=False).encode('utf-8')

        csv_para_download = converter_df_para_csv(df)

        st.download_button(
            label="📥 Baixar arquivo anonimizado (CSV)",
            data=csv_para_download,
            file_name="resultado_anonimizado.csv",
            mime='text/csv',
        )
