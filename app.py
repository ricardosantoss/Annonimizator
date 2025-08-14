import streamlit as st
import pandas as pd
import pickle
import spacy
from spacy.language import Language

# --- Configuração da Página e Constantes ---
st.set_page_config(page_title="Ferramenta de Anonimização Híbrida", layout="wide")
NOME_ARQUIVO_ORIGINAL = "Data_LLMs_and_Gold_and_EHRs.pkl"
COLUNA_ALVO = "25. Evolução Alta"
COLUNA_ANONIMIZADA = "texto_anonimizado"

# --- Funções ---

@st.cache_resource
def carregar_modelo_spacy() -> Language:
    """Carrega o modelo de NLP do spaCy, essencial para a IA."""
    return spacy.load('pt_core_news_lg')

@st.cache_data
def carregar_dados_locais(caminho_arquivo: str) -> pd.DataFrame:
    """Carrega o DataFrame do arquivo .pkl."""
    try:
        return pd.read_pickle(caminho_arquivo)
    except FileNotFoundError:
        st.error(f"Erro: O arquivo '{caminho_arquivo}' não foi encontrado no repositório.")
        return None

# >>> NOVA FUNÇÃO: Lógica de anonimização com IA <<<
def anonimizar_texto_com_ia(texto: str, nlp_model: Language) -> str:
    """Aplica o modelo de NER para encontrar e substituir Pessoas (PER) e Locais (LOC)."""
    if not isinstance(texto, str) or texto.strip() == "":
        return ""
    
    doc = nlp_model(texto)
    texto_anonimizado = texto
    
    for entidade in reversed(doc.ents):
        if entidade.label_ in ['PER', 'LOC']:
            texto_anonimizado = texto_anonimizado[:entidade.start_char] + f'<{entidade.label_}>' + texto_anonimizado[entidade.end_char:]
    
    return texto_anonimizado

# --- Inicialização ---
nlp = carregar_modelo_spacy() # Carrega o modelo de IA

if 'df_trabalho' not in st.session_state:
    df_original = carregar_dados_locais(NOME_ARQUIVO_ORIGINAL)
    if df_original is not None:
        st.session_state.df_trabalho = df_original.copy()
        if COLUNA_ANONIMIZADA not in st.session_state.df_trabalho.columns:
             st.session_state.df_trabalho[COLUNA_ANONIMIZADA] = st.session_state.df_trabalho[COLUNA_ALVO]
    else:
        st.session_state.df_trabalho = None

# --- Interface Principal ---
st.title("Ferramenta de Anonimização Híbrida (IA + Humano) 🤖👨‍💻")

if st.session_state.df_trabalho is not None:
    df = st.session_state.df_trabalho
    total_rows = len(df)
    
    col_main, col_sidebar = st.columns([3, 1])

    # --- Coluna da Direita (Controles) ---
    with col_sidebar:
        st.header("Controles")

        # >>> NOVO: Botão para acionar a IA <<<
        if st.button("🤖 Pré-anonimizar TUDO com IA", use_container_width=True, help="A IA irá analisar a coluna original e preencher a coluna de edição com uma primeira versão anonimizada. Você poderá então revisar e corrigir."):
            with st.spinner("A IA está analisando todos os registros... Isso pode levar um minuto."):
                df[COLUNA_ANONIMIZADA] = df[COLUNA_ALVO].apply(lambda texto: anonimizar_texto_com_ia(texto, nlp))
            st.success("Pré-anonimização com IA concluída! Agora revise os resultados.")
        
        st.write("---")
        
        st.metric(label="Progresso da Revisão", value=f"{st.session_state.current_index + 1} / {total_rows}")
        st.write("**Navegação:**")
        col_prev, col_next = st.columns(2)
        prev_pressed = col_prev.button("⬅️ Anterior", use_container_width=True)
        next_pressed = col_next.button("Próximo ➡️", use_container_width=True, type="primary")
        
        st.write("---")

        st.write("**Download dos Dados Finais:**")
        # ... (código de download permanece o mesmo) ...
        @st.cache_data
        def converter_df_para_csv(dataframe):
            return dataframe.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        @st.cache_data
        def converter_df_para_pkl(dataframe):
            return pickle.dumps(dataframe)
        csv_para_download = converter_df_para_csv(df)
        pkl_para_download = converter_df_para_pkl(df)
        st.download_button("📥 Baixar como CSV", csv_para_download, "dados_anonimizados.csv", 'text/csv', use_container_width=True)
        st.download_button("💾 Baixar como PKL", pkl_para_download, NOME_ARQUIVO_ORIGINAL, 'application/octet-stream', use_container_width=True)

    # --- Coluna Principal (Edição) ---
    with col_main:
        # (O código da coluna principal para edição e navegação permanece exatamente o mesmo da versão anterior)
        st.header(f"Revisando Registro: {st.session_state.current_index + 1}")

        texto_editado_atual = str(df.loc[st.session_state.current_index, COLUNA_ANONIMIZADA]) if pd.notna(df.loc[st.session_state.current_index, COLUNA_ANONIMIZADA]) else ""

        texto_atualizado = st.text_area(
            label=f"Conteúdo para revisão (original na coluna '{COLUNA_ALVO}'):",
            value=texto_editado_atual,
            height=500,
            key=f"editor_{st.session_state.current_index}"
        )
        st.session_state.df_trabalho.loc[st.session_state.current_index, COLUNA_ANONIMIZADA] = texto_atualizado

        # (Lógica de navegação permanece a mesma)
        if prev_pressed or next_pressed:
            if prev_pressed and st.session_state.current_index > 0:
                st.session_state.current_index -= 1
            if next_pressed and st.session_state.current_index < total_rows - 1:
                st.session_state.current_index += 1
            st.rerun()

else:
    st.error("Não foi possível carregar o DataFrame.")
