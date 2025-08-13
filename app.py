import streamlit as st
import pandas as pd

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# -----------------------------------------------------------------------------

st.set_page_config(page_title="Visualizador de Dados", layout="wide")

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

# Carrega o DataFrame do arquivo local
# Substitua o nome do arquivo se for diferente
df = carregar_dados_locais("Data_LLMs_and_Gold_and_EHRs.pkl")

# -----------------------------------------------------------------------------
# INTERFACE DA APLICAÇÃO STREAMLIT
# -----------------------------------------------------------------------------

st.title("VISUALIZADOR E EXPORTADOR DE DADOS 📊")
st.markdown("""
Esta aplicação carrega e exibe os dados do arquivo `.pkl` que está no repositório do GitHub.
Você pode visualizar a tabela abaixo e usar o botão de download para exportá-la como um arquivo CSV.
""")

# Só continua se o DataFrame foi carregado com sucesso
if df is not None:
    st.success(f"Arquivo de dados carregado com sucesso! ({len(df)} linhas)")

    # Exibe o DataFrame completo na tela
    st.dataframe(df)

    # Prepara o arquivo para download
    @st.cache_data
    def converter_df_para_csv(dataframe):
        # Converte o DataFrame para CSV em memória, usando codificação UTF-8
        return dataframe.to_csv(index=False).encode('utf-8')

    csv_para_download = converter_df_para_csv(df)

    # Botão de download
    st.download_button(
        label="📥 Baixar dados como CSV",
        data=csv_para_download,
        file_name="dados_exportados.csv",
        mime='text/csv',
    )
else:
    st.warning("Aguardando o carregamento dos dados ou verifique o erro acima.")
