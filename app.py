import streamlit as st
import pandas as pd
import pickle

# --- Configuração da Página e Constantes ---
st.set_page_config(page_title="Ferramenta de Anonimização Rápida", layout="wide")
NOME_ARQUIVO_ORIGINAL = "Data_LLMs_and_Gold_and_EHRs.pkl"
COLUNA_ALVO = "25. Evolução Alta"
COLUNA_ANONIMIZADA = "texto_anonimizado"

# --- Funções ---
@st.cache_data
def carregar_dados_locais(caminho_arquivo: str) -> pd.DataFrame:
    """Carrega o DataFrame do arquivo .pkl e o armazena em cache."""
    try:
        return pd.read_pickle(caminho_arquivo)
    except FileNotFoundError:
        st.error(f"Erro: O arquivo '{caminho_arquivo}' não foi encontrado no repositório.")
        return None

# --- Inicialização do Estado da Aplicação ---
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0

if 'df_trabalho' not in st.session_state:
    df_original = carregar_dados_locais(NOME_ARQUIVO_ORIGINAL)
    if df_original is not None:
        st.session_state.df_trabalho = df_original.copy()
        # Se a coluna de anonimização ainda não existe, cria ela
        if COLUNA_ANONIMIZADA not in st.session_state.df_trabalho.columns:
             st.session_state.df_trabalho[COLUNA_ANONIMIZADA] = st.session_state.df_trabalho[COLUNA_ALVO]
    else:
        st.session_state.df_trabalho = None

# --- Interface Principal ---
st.title("Ferramenta de Anonimização Rápida ⚡")
st.markdown("Navegue, clique nas tags para inseri-las e edite o texto. Suas alterações são salvas automaticamente ao navegar.")

if st.session_state.df_trabalho is not None:
    df = st.session_state.df_trabalho
    total_rows = len(df)
    
    col_main, col_sidebar = st.columns([3, 1])

    # --- Coluna da Direita (Controles e Navegação) ---
    with col_sidebar:
        st.header("Controles")
        st.metric(label="Progresso", value=f"{st.session_state.current_index + 1} / {total_rows}")

        st.write("**Navegação:**")
        col_prev, col_next = st.columns(2)
        prev_pressed = col_prev.button("⬅️ Anterior", use_container_width=True)
        next_pressed = col_next.button("Próximo ➡️", use_container_width=True, type="primary")
        
        st.write("---")

        st.write("**Download dos Dados Editados:**")
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
        st.header(f"Editando Registro: {st.session_state.current_index + 1}")
        
        # Pega o texto atual da linha que estamos editando
        texto_editado_atual = df.loc[st.session_state.current_index, COLUNA_ANONIMIZADA]

        # --- NOVA SEÇÃO: BOTÕES DE TAGS RÁPIDAS ---
        st.write("**Clique para inserir uma tag:**")
        tags = ["<NOME>", "<DATA>", "<HOSPITAL>", "<CIDADE>", "<TELEFONE>", "<ENDEREÇO>", "<CPF>", "<OUTRO_DADO>"]
        
        # Cria colunas para os botões ficarem bem organizados
        cols = st.columns(len(tags))
        for i, tag in enumerate(tags):
            if cols[i].button(tag, use_container_width=True):
                # Quando um botão é clicado, adiciona a tag ao final do texto atual
                texto_editado_atual += f" {tag}"
        
        st.write("---")

        # A área de texto agora é controlada pela variável
        texto_atualizado = st.text_area(
            label=f"Conteúdo da coluna '{COLUNA_ALVO}':",
            value=texto_editado_atual,
            height=400,
            key=f"editor_{st.session_state.current_index}"
        )
        
        # Atualiza o DataFrame com o texto da caixa de edição (que pode ter sido modificado pelos botões ou pelo teclado)
        st.session_state.df_trabalho.loc[st.session_state.current_index, COLUNA_ANONIMIZADA] = texto_atualizado

    # --- Lógica de Navegação ---
    # A lógica de salvar já aconteceu. Agora só navegamos.
    if prev_pressed:
        if st.session_state.current_index > 0:
            st.session_state.current_index -= 1
            st.rerun()

    if next_pressed:
        if st.session_state.current_index < total_rows - 1:
            st.session_state.current_index += 1
            st.rerun()
else:
    st.error("Não foi possível carregar o DataFrame. Verifique o arquivo de dados no repositório.")
