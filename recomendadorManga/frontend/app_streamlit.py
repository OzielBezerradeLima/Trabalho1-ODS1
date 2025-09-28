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
    
    # MODIFICAÇÃO AQUI: Usar selectbox para o nome do mangá
    manga_titles = items_df["title"].tolist()
    selected_manga_title = st.selectbox("Nome do Mangá", manga_titles)
    
    # Obter o item_id correspondente ao nome do mangá selecionado
    new_item_id = items_df[items_df["title"] == selected_manga_title]["item_id"].iloc[0]
    st.write(f"ID do Mangá Selecionado: {new_item_id}") # Para visualização, pode remover depois

    new_rating = st.slider("Nota do Mangá", min_value=1, max_value=5, value=3)
    
    if st.button("Salvar Avaliação"):
        # Verifica se o usuário já avaliou o mangá
        exists_index = ratings_df[
            (ratings_df["user_id"] == new_user_id) &
            (ratings_df["item_id"] == new_item_id)
        ].index

        if len(exists_index) > 0:
            # Atualiza a nota existente
            ratings_df.loc[exists_index, "rating"] = new_rating
            st.success(f"Avaliação atualizada: Usuário {new_user_id}, Mangá {new_item_id}, Nota {new_rating}")
        else:
            new_row = {"user_id": new_user_id, "item_id": new_item_id, "rating": new_rating}
            # Atualizar o dataframe na sessão
            ratings_df = pd.concat([ratings_df, pd.DataFrame([new_row])], ignore_index=True)
            st.success(f"Avaliação adicionada: Usuário {new_user_id}, Mangá {new_item_id}, Nota {new_rating}")
        
        # Atualiza CSV
        ratings_df.to_csv(RATINGS_CSV, index=False)

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

    st.subheader(selected_item["title"])
    st.write(f"Categoria: {selected_item['category']}")
    if "author" in items_with_avg.columns:
        st.write(f"Autor: {selected_item['author']}")
    if "year" in items_with_avg.columns:
        st.write(f"Ano: {selected_item['year']}")
    st.write(f"Média de Avaliação: {selected_item['avg_rating']:.2f}")

    user_for_rec = st.number_input("Seu ID de usuário para recomendações", min_value=1, step=1)
    top_n_rec = st.slider("Quantos mangás recomendar", 1, 5, 3)

    if st.button("Recomendar para mim"):
        try:
            response = requests.get(f"{API_URL}/{user_for_rec}", params={"top_n": top_n_rec})
            if response.status_code == 200:
                recs = response.json()["recommendations"]
                if recs:
                    rec_df = pd.DataFrame(recs)
                    st.subheader(f"Recomendações para Usuário {user_for_rec}")
                    st.table(rec_df[["item_id", "title", "category", "score"]])
                else:
                    st.warning("Nenhuma recomendação encontrada para este usuário.")
            else:
                st.error("Erro ao conectar ao backend")
        except Exception as e:
            st.error(f"Erro: {e}")
