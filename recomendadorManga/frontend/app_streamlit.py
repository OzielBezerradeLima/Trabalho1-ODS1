import streamlit as st
import pandas as pd
import os
import requests
import urllib3

# Desativar avisos de SSL que podem aparecer no terminal
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Caminhos dos CSVs do backend
ITEMS_CSV = "../backend/items.csv"
RATINGS_CSV = "../backend/ratings.csv"
API_URL = "http://127.0.0.1:8000/recomendar"

# Cabeçalho para simular um navegador e evitar bloqueios (erro 403)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# --- Usar cache para acelerar o carregamento dos dados ---
@st.cache_data
def load_data():
    items = pd.read_csv(ITEMS_CSV)
    if os.path.exists(RATINGS_CSV):
        ratings = pd.read_csv(RATINGS_CSV)
        ratings["user_id"] = pd.to_numeric(ratings["user_id"], errors="coerce").fillna(0).astype(int)
        ratings["item_id"] = pd.to_numeric(ratings["item_id"], errors="coerce").fillna(0).astype(int)
        ratings["rating"] = pd.to_numeric(ratings["rating"], errors="coerce").fillna(0).astype(int)
    else:
        ratings = pd.DataFrame(columns=["user_id", "item_id", "rating"])
    
    # Calcular média de avaliações
    avg_ratings = ratings.groupby("item_id")["rating"].mean().reset_index()
    items_with_avg = items.merge(avg_ratings, on="item_id", how="left")
    items_with_avg['rating'] = items_with_avg['rating'].fillna(0)
    items_with_avg.rename(columns={"rating": "avg_rating"}, inplace=True)
    
    return items_with_avg, ratings

items_with_avg, ratings_df = load_data()


# Streamlit Tabs
tab1, tab2, tab3 = st.tabs([
    "➕ Adicionar Usuário/Avaliação",
    "📚 Gerar Recomendações",
    "🏠 Catálogo de Mangás"
])

# -------------------------------------
# Tab 1: Adicionar Usuário/Avaliação
# -------------------------------------
with tab1:
    st.header("Adicionar Usuário e Avaliação de Mangá")
    
    new_user_id = st.number_input("ID do Usuário", min_value=1, step=1)
    new_item_id = st.number_input("ID do Mangá", min_value=1, step=1)
    new_rating = st.slider("Nota do Mangá", min_value=1, max_value=5, value=3)
    
    if st.button("Adicionar Avaliação"):
        exists = ((ratings_df["user_id"] == new_user_id) & 
                  (ratings_df["item_id"] == new_item_id)).any()
        if exists:
            st.warning("Este usuário já avaliou este mangá!")
        else:
            new_row = {"user_id": new_user_id, "item_id": new_item_id, "rating": new_rating}
            # Atualizar o dataframe na sessão
            ratings_df = pd.concat([ratings_df, pd.DataFrame([new_row])], ignore_index=True)
            # Guardar no ficheiro CSV
            ratings_df.to_csv(RATINGS_CSV, index=False)
            st.success(f"Avaliação adicionada: Usuário {new_user_id}, Mangá {new_item_id}, Nota {new_rating}")
            # Limpar o cache para que os dados sejam recarregados na próxima interação
            st.cache_data.clear()

    st.subheader("Avaliações existentes")
    st.dataframe(ratings_df)

# -------------------------------------
# Tab 2: Gerar Recomendações
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
                response = requests.get(f"{API_URL}/{selected_user}", params={"top_n": top_n})
                if response.status_code == 200:
                    recs = response.json()["recommendations"]
                    if recs:
                        rec_df = pd.DataFrame(recs)
                        st.subheader(f"Recomendações para Usuário {selected_user}")
                        st.table(rec_df[["item_id", "title", "category", "score"]])
                    else:
                        st.warning("Nenhuma recomendação encontrada para este usuário.")
                else:
                    st.error(f"Erro ao conectar ao backend: {response.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"Erro de conexão: {e}")

# -------------------------------------
# Tab 3: Catálogo de Mangás
# -------------------------------------
with tab3:
    st.header("Catálogo de Mangás")
    
    manga_titles = items_with_avg["title"].tolist()
    selected_title = st.selectbox("Selecione um Mangá para ver os detalhes", manga_titles)
    
    selected_item = items_with_avg[items_with_avg["title"] == selected_title].iloc[0]

    st.markdown("---")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        image_url = selected_item.get("image_url")
        if image_url and pd.notna(image_url):
            # Tentar carregar a imagem diretamente do URL
            st.image(image_url, caption=selected_item["title"], use_container_width=True)
        else:
            st.warning("URL da imagem não disponível.")

    with col2:
        st.subheader(selected_item["title"])
        st.write(f"**Categoria:** {selected_item['category']}")
        if "author" in items_with_avg.columns and pd.notna(selected_item['author']):
            st.write(f"**Autor:** {selected_item['author']}")
        if "year" in items_with_avg.columns and pd.notna(selected_item['year']):
            # Assegurar que o ano é um inteiro antes de mostrar
            try:
                st.write(f"**Ano:** {int(selected_item['year'])}")
            except (ValueError, TypeError):
                st.write(f"**Ano:** {selected_item['year']}")
        st.write(f"**Média de Avaliação:** {selected_item['avg_rating']:.2f}")