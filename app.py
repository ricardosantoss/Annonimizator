import streamlit as st
import pandas as pd
import spacy
from spacy.language import Language

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA E DO MODELO DE IA
# -----------------------------------------------------------------------------

# Configura o título e o ícone da página do Streamlit
st.set_page_config(page_title="Anonimizador de Notas de Alta", layout="wide")

@st.cache_resource
def carregar_modelo_spacy() -> Language:
    """
    Carrega o modelo de NLP do spaCy.
    Usa o cache do Streamlit para não recarregar o modelo a cada interação.
    """
    st.write("Carregando modelo de linguagem (spaCy)... Isso pode levar alguns segundos.")
    # Carrega o modelo de português treinado para reconhecer entidades
    modelo = spacy.load('pt_core_news_lg')
    st.write("✅ Modelo carregado com sucesso!")
    return modelo

# Carrega o modelo assim que a aplicação inicia
nlp = carregar_modelo_spacy()

# -----------------------------------------------------------------------------
# FUNÇÃO DE ANONIMIZAÇÃO
# -----------------------------------------------------------------------------

def anonimizar_texto(texto: str) -> str:
    """
    Aplica o modelo de NER para encontrar e substituir Pessoas (PER) e Locais (LOC).
    """
    # Garante que o texto seja uma string válida
    if not isinstance(texto, str) or texto.strip() == "":
        return texto

    doc = nlp(texto)
    texto_anonimizado = texto

    # Itera sobre as entidades encontradas (de trás para frente para evitar erros de índice)
    for entidade in reversed(doc.ents):
        if entidade.label_ in ['PER', 'LOC']:
            # Substitui o texto da entidade por um placeholder [LABEL_REMOVIDO]
            texto_anonimizado = texto_anonimizado[:entidade.start_char] + f'[{entidade.label_}]' + texto_anonimizado[entidade.end_char:]
    
    return texto_anonimizado

# -----------------------------------------------------------------------------
# INTERFACE DA APLICAÇÃO STREAMLIT
# -----------------------------------------------------------------------------

st.title("FERRAMENTA DE ANONIMIZAÇÃO DE NOTAS DE ALTA 🩺 anonimizador de notas")
st.markdown("""
Esta ferramenta utiliza Inteligência Artificial para identificar e remover **nomes de pessoas (PER)** e **locais (LOC)** de textos.

**Instruções:**
1.  Faça o upload do seu arquivo (CSV ou Excel).
2.  Selecione a coluna que contém o texto a ser anonimizado.
3.  Clique no botão para iniciar o processo.
4.  Revise o resultado e faça o download do arquivo modificado.

⚠️ **Atenção:** A anonimização automática não é perfeita. **É fundamental que um humano revise o resultado final** para garantir que nenhuma informação sensível tenha permanecido.
""")

# Componente para upload de arquivo
uploaded_file = st.file_uploader(
    "1. Escolha seu arquivo (CSV ou Excel)",
    type=['csv', 'xlsx']
)

# Só continua se um arquivo foi enviado
if uploaded_file is not None:
    try:
        # Tenta ler o arquivo dependendo da sua extensão
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.success(f"Arquivo '{uploaded_file.name}' carregado com sucesso!")
        
        # Permite ao usuário selecionar a coluna para anonimizar
        colunas = df.columns.tolist()
        # Tenta pré-selecionar a coluna "25. Evolução de Alta" se ela existir
        try:
            default_index = colunas.index("25. Evolução Alta")
        except ValueError:
            default_index = 0
            
        coluna_selecionada = st.selectbox(
            "2. Selecione a coluna com o texto para anonimizar:",
            colunas,
            index=default_index
        )
        
        st.write("Amostra da coluna selecionada:")
        st.dataframe(df[[coluna_selecionada]].head())

        # Botão para iniciar o processo de anonimização
        if st.button("🚀 Iniciar Anonimização", type="primary"):
            
            # Cria a nova coluna com o resultado
            nova_coluna_nome = f"anonimizado_{coluna_selecionada}"

            with st.spinner(f"Anonimizando {len(df)} linhas... Este processo pode levar alguns minutos."):
                # Usa .apply() para executar a função em cada linha da coluna
                df[nova_coluna_nome] = df[coluna_selecionada].apply(anonimizar_texto)
            
            st.success("Processo de anonimização concluído!")
            
            st.write("Amostra do resultado (colunas original e anonimizada):")
            st.dataframe(df[[coluna_selecionada, nova_coluna_nome]].head())
            
            # Prepara o arquivo para download
            @st.cache_data
            def converter_df_para_csv(dataframe):
                # Converte o DataFrame para CSV em memória, usando codificação UTF-8
                return dataframe.to_csv(index=False).encode('utf-8')

            csv_para_download = converter_df_para_csv(df)

            # Botão de download
            st.download_button(
                label="📥 Baixar arquivo anonimizado (CSV)",
                data=csv_para_download,
                file_name=f"anonimizado_{uploaded_file.name.split('.')[0]}.csv",
                mime='text/csv',
            )

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo: {e}")
