import streamlit as st
import pandas as pd
import os
import requests
import urllib3
import altair as alt

# Desativar avisos de SSL que podem aparecer no terminal
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Inicializa o estado da sessão para controle de página ---
if 'selected_manga_id' not in st.session_state:
    st.session_state.selected_manga_id = None

# Caminhos dos CSVs do backend
ITEMS_CSV = "../backend/items.csv"
RATINGS_CSV = "../backend/ratings.csv"
API_URL = "http://127.0.0.1:8000"

# -------------------------
# Carregar dados
# -------------------------
# Esta linha é necessária para a Tab 1 funcionar como desenhou
items_df = pd.read_csv(ITEMS_CSV)
api_acuracia_url = f"{API_URL}/avaliar_acuracia"

@st.cache_data
def load_data():
    """Carrega e processa os dataframes de itens e avaliações."""
    # Reutiliza o items_df já carregado
    items = items_df.copy()
    
    if os.path.exists(RATINGS_CSV):
        ratings = pd.read_csv(RATINGS_CSV)
        ratings["user_id"] = pd.to_numeric(ratings["user_id"], errors="coerce").fillna(0).astype(int)
        ratings["item_id"] = pd.to_numeric(ratings["item_id"], errors="coerce").fillna(0).astype(int)
        ratings["rating"] = pd.to_numeric(ratings["rating"], errors="coerce").fillna(0).astype(int)
    else:
        ratings = pd.DataFrame(columns=["user_id", "item_id", "rating"])

    # Calcular média de avaliações por mangá
    avg_ratings = ratings.groupby("item_id")["rating"].mean().reset_index()
    items_with_avg = items.merge(avg_ratings, on="item_id", how="left")
    # Preencher com 0 apenas a coluna de avaliação média para evitar erros de cálculo
    items_with_avg['rating'] = items_with_avg['rating'].fillna(0)
    items_with_avg.rename(columns={"rating": "avg_rating"}, inplace=True)
    
    return items_with_avg, ratings

items_with_avg, ratings_df = load_data()

# -------------------------
# Streamlit Tabs
# -------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "➕ Adicionar/Atualizar Avaliação",
    "📚 Gerar Recomendações",
    "📊 Avaliar Acurácia",
    "🏠 Catálogo de Mangás"
])

# -------------------------------------
# Tab 1: Adicionar Usuário/Avaliação (O SEU CÓDIGO)
# -------------------------------------
with tab1:
    st.header("Adicionar Usuário e Avaliação de Mangá")
    
    new_user_id = st.number_input("ID do Usuário", min_value=1, step=1)
    
    manga_titles = items_df["title"].tolist()
    selected_manga_title = st.selectbox("Nome do Mangá", manga_titles)
    
    new_item_id = items_df[items_df["title"] == selected_manga_title]["item_id"].iloc[0]
    st.write(f"ID do Mangá Selecionado: {new_item_id}")

    new_rating = st.slider("Nota do Mangá", min_value=1, max_value=5, value=3)
    
    if st.button("Salvar Avaliação"):
        exists_index = ratings_df[
            (ratings_df["user_id"] == new_user_id) &
            (ratings_df["item_id"] == new_item_id)
        ].index

        if len(exists_index) > 0:
            ratings_df.loc[exists_index, "rating"] = new_rating
            st.success(f"Avaliação atualizada: Usuário {new_user_id}, Mangá {new_item_id}, Nota {new_rating}")
        else:
            new_row = {"user_id": new_user_id, "item_id": new_item_id, "rating": new_rating}
            ratings_df = pd.concat([ratings_df, pd.DataFrame([new_row])], ignore_index=True)
            st.success(f"Avaliação adicionada: Usuário {new_user_id}, Mangá {new_item_id}, Nota {new_rating}")
        
        ratings_df.to_csv(RATINGS_CSV, index=False)
        st.cache_data.clear() # Limpa o cache para recarregar os dados

    st.subheader("Avaliações existentes")
    st.dataframe(ratings_df)

# -------------------------------------
# Tab 2: Gerar Recomendações (O SEU CÓDIGO)
# -------------------------------------
with tab2:
    st.header("Gerar Recomendações")
    
    if ratings_df.empty:
        st.info("Adicione algumas avaliações primeiro na aba 'Adicionar Usuário/Avaliação'.")
    else:
        user_ids = ratings_df["user_id"].unique()
        selected_user = st.selectbox(
            "Escolha o ID do Usuário",
            options=sorted(user_ids)
        )
        top_n = st.slider("Quantidade de Recomendações", 1, 10, 5)
        
        if st.button("Gerar Recomendações"):
            try:
                response = requests.get(f"{API_URL}/recomendar/{selected_user}", params={"top_n": top_n})
                if response.status_code == 200:
                    recs = response.json()["recommendations"]
                    if recs:
                        rec_df = pd.DataFrame(recs)
                        st.subheader(f"Recomendações para Usuário {selected_user}")
                        
                        rec_df = rec_df.merge(items_df[['item_id', 'image_url']], on='item_id', how='left')
                        
                        # Limitar o número de colunas para melhor visualização
                        num_recs = len(rec_df)
                        cols = st.columns(num_recs if num_recs <= 5 else 5)
                        for i, (_, row) in enumerate(rec_df.iterrows()):
                            with cols[i % len(cols)]:
                                if pd.notna(row['image_url']):
                                    st.image(row['image_url'], caption=row['title'])
                                st.write(f"**Score:** {row['score']:.2f}")

                        st.subheader("Visualização dos Scores de Recomendação")
                        chart = alt.Chart(rec_df).mark_bar().encode(
                            x=alt.X('title', sort='-y', title='Título do Mangá'),
                            y=alt.Y('score', title='Score de Recomendação'),
                            tooltip=['title', 'score']
                        ).properties(
                            title='Top Recomendações por Score'
                        )
                        st.altair_chart(chart, use_container_width=True)

                    else:
                        st.warning("Nenhuma recomendação encontrada para este usuário.")
                else:
                    st.error("Erro ao conectar ao backend")
            except Exception as e:
                st.error(f"Erro: {e}")

# -------------------------------------
# Tab 3: Avaliar Acurácia (O SEU CÓDIGO)
# -------------------------------------
with tab3:
    st.header("Avaliação da Acurácia do Modelo")
    
    if ratings_df.empty or len(ratings_df['user_id'].unique()) < 1:
        st.info("Adicione mais avaliações para calcular a acurácia.")
    else:
        selected_user_accuracy = st.number_input(
            "Escolha o ID do Usuário para avaliação", 
            min_value=int(ratings_df["user_id"].min()), 
            max_value=int(ratings_df["user_id"].max()), 
            step=1, 
            value=int(ratings_df["user_id"].min())
        )
        test_fraction = st.slider("Fração de avaliações para teste", 0.1, 0.9, 0.5, step=0.1)
        top_n_accuracy = st.slider("Quantidade de recomendações para avaliação", 1, 10, 5)
        
        if st.button("Calcular Acurácia"):
            try:
                response = requests.get(f"{API_URL}/avaliar_acuracia/{selected_user_accuracy}",
                                        params={"top_n": top_n_accuracy, "test_fraction": test_fraction})
                
                if response.status_code == 200:
                    result = response.json()
                    if "message" in result:
                        st.warning(result["message"])
                    else:
                        st.subheader(f"Resultados de Acurácia para o Usuário {result['user_id']}")
                        st.metric(label="Acurácia", value=f"{result['accuracy']:.2%}")
                        st.write(f"**Itens avaliados positivamente no teste:** {result['test_liked']}")
                        st.write(f"**Itens recomendados:** {result['recommended']}")
                        st.write(f"**Itens corretos (hits):** {result['hits']}")
                else:
                    st.error("Erro ao conectar ao backend")
            except Exception as e:
                st.error(f"Erro: {e}")

# -------------------------------------
# Tab 4: Catálogo de Mangás (MODIFICADO)
# -------------------------------------
with tab4:
    st.header("Catálogo de Mangás")
    
    # Selectbox para escolher o mangá pelo título
    manga_titles_catalog = sorted(items_with_avg["title"].tolist())
    selected_title_catalog = st.selectbox(
        "Selecione um Mangá para ver os detalhes",
        manga_titles_catalog,
        key="catalog_selectbox"
    )
    
    # Obter os dados do item selecionado
    selected_item = items_with_avg[items_with_avg["title"] == selected_title_catalog].iloc[0]

    st.markdown("---")
    
    # Layout de duas colunas para os detalhes
    col1, col2 = st.columns([1, 2])
    
    # Coluna da esquerda para a imagem
    with col1:
        image_url = selected_item.get("image_url")
        if image_url and pd.notna(image_url):
            st.image(image_url, caption=selected_item["title"], use_container_width=True)
        else:
            st.warning("Imagem não disponível.")

    # Coluna da direita para as informações
    with col2:
        st.subheader(selected_item["title"])
        st.write(f"**Categoria:** {selected_item['category']}")
        if "author" in selected_item and pd.notna(selected_item['author']):
            st.write(f"**Autor:** {selected_item['author']}")
        if "year" in selected_item and pd.notna(selected_item['year']):
            try:
                st.write(f"**Ano:** {int(selected_item['year'])}")
            except (ValueError, TypeError):
                 st.write(f"**Ano:** {selected_item['year']}")
        st.write(f"**Média de Avaliação:** ⭐ {selected_item['avg_rating']:.2f}")

