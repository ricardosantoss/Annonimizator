import streamlit as st
import pandas as pd

# --- Configuração da Página ---
st.set_page_config(page_title="Ferramenta de Anonimização Manual", layout="wide")

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

# O st.session_state é a memória da nossa aplicação.
# Vamos inicializar as variáveis que precisamos se elas ainda não existirem.
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0

if 'df_trabalho' not in st.session_state:
    # Carregamos o DataFrame original uma vez
    df_original = carregar_dados_locais("Data_LLMs_and_Gold_and_EHRs.pkl")
    if df_original is not None:
        # Criamos uma cópia de trabalho e adicionamos a coluna para o texto anonimizado
        st.session_state.df_trabalho = df_original.copy()
        st.session_state.df_trabalho['texto_anonimizado'] = ''
    else:
        st.session_state.df_trabalho = None

# --- Interface Principal ---

st.title("Ferramenta de Anonimização Assistida ✍️")
st.markdown("Navegue pelos registros um a um, edite o texto e salve suas alterações.")

# Garante que a aplicação só continue se o DataFrame foi carregado com sucesso
if st.session_state.df_trabalho is not None:
    df = st.session_state.df_trabalho
    total_rows = len(df)
    
    # Define a coluna que queremos exibir e editar
    COLUNA_ALVO = "25. Evolução Alta" 

    # --- Layout da Interface em Colunas ---
    col_main, col_sidebar = st.columns([3, 1])

    with col_sidebar:
        st.header("Controles")
        
        # Exibe o progresso atual
        st.metric(label="Progresso", value=f"{st.session_state.current_index + 1} / {total_rows}")

        # Botões de navegação
        st.write("**Navegação:**")
        col_prev, col_next = st.columns(2)
        
        # A lógica dos botões será tratada mais abaixo
        prev_pressed = col_prev.button("⬅️ Anterior", use_container_width=True)
        next_pressed = col_next.button("Próximo ➡️", use_container_width=True, type="primary")
        
        st.write("---")

        # Funcionalidade de "Tags Rápidas" para copiar e colar
        with st.expander("Tags rápidas para copiar"):
            st.code("<NOME>", language="")
            st.code("<NOME_SOCIAL>", language="")
            st.code("<DATA>", language="")
            st.code("<TELEFONE>", language="")
            st.code("<ENDEREÇO>", language="")
            st.code("<CIDADE>", language="")
            st.code("<HOSPITAL>", language="")
            st.code("<CPF>", language="")
            st.code("<OUTRO_DADO>", language="")
        
        st.write("---")
        
        # Funcionalidade de Download
        @st.cache_data
        def converter_df_para_csv(dataframe):
            return dataframe.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')

        csv_para_download = converter_df_para_csv(df)
        
        st.download_button(
            label="📥 Baixar dados (CSV)",
            data=csv_para_download,
            file_name="dados_anonimizados.csv",
            mime='text/csv',
            use_container_width=True
        )

    with col_main:
        st.header(f"Editando Registro: {st.session_state.current_index + 1}")
        
        # Pega o texto original e o texto já editado (se existir)
        texto_original = df.loc[st.session_state.current_index, COLUNA_ALVO]
        texto_editado = df.loc[st.session_state.current_index, 'texto_anonimizado']

        # O valor inicial da área de texto é o texto já editado, ou o original se a edição não começou
        valor_inicial = texto_editado if texto_editado else texto_original
        
        # Área de texto para edição. O 'key' é crucial para que o Streamlit rastreie seu conteúdo.
        texto_atualizado = st.text_area(
            label=f"Conteúdo da coluna '{COLUNA_ALVO}':",
            value=valor_inicial,
            height=400,
            key=f"editor_{st.session_state.current_index}" # Chave única para cada registro
        )

    # --- Lógica de Navegação e Salvamento ---
    
    # PRIMEIRO, salvamos o trabalho atual ANTES de mudar de página
    df.loc[st.session_state.current_index, 'texto_anonimizado'] = texto_atualizado

    # AGORA, processamos a navegação
    if prev_pressed:
        if st.session_state.current_index > 0:
            st.session_state.current_index -= 1
            st.rerun() # st.rerun() força a atualização da página para o novo índice

    if next_pressed:
        if st.session_state.current_index < total_rows - 1:
            st.session_state.current_index += 1
            st.rerun()

else:
    st.error("Não foi possível carregar o DataFrame. Verifique o arquivo de dados no repositório.")
