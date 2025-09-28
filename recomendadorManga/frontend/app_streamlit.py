import streamlit as st
import pandas as pd
import os
import requests

# Caminhos dos CSVs do backend
ITEMS_CSV = "../backend/items.csv"
RATINGS_CSV = "../backend/ratings.csv"
API_URL = "http://127.0.0.1:8000/recomendar"

# -------------------------
# Carregar dados
# -------------------------
items_df = pd.read_csv(ITEMS_CSV)

if os.path.exists(RATINGS_CSV):
    ratings_df = pd.read_csv(RATINGS_CSV)
    # Garantir que os IDs e ratings sejam inteiros
    ratings_df["user_id"] = pd.to_numeric(ratings_df["user_id"], errors="coerce").fillna(0).astype(int)
    ratings_df["item_id"] = pd.to_numeric(ratings_df["item_id"], errors="coerce").fillna(0).astype(int)
    ratings_df["rating"] = pd.to_numeric(ratings_df["rating"], errors="coerce").fillna(0).astype(int)
else:
    ratings_df = pd.DataFrame(columns=["user_id", "item_id", "rating"])

# Calcular média de avaliações por mangá
avg_ratings = ratings_df.groupby("item_id")["rating"].mean().reset_index()
items_with_avg = items_df.merge(avg_ratings, on="item_id", how="left").fillna(0)
items_with_avg.rename(columns={"rating": "avg_rating"}, inplace=True)

# -------------------------
# Streamlit Tabs
# -------------------------
tab1, tab2, tab3 = st.tabs([
    "➕ Adicionar/Atualizar Avaliação",
    "📚 Gerar Recomendações",
    "🏠 Catálogo de Mangás"
])

# -------------------------------------
# Tab 1: Adicionar/Atualizar Avaliação
# -------------------------------------
with tab1:
    st.header("Adicionar ou Atualizar Avaliação de Mangá")
    
    new_user_id = st.number_input("ID do Usuário", min_value=1, step=1)
    new_item_id = st.number_input("ID do Mangá", min_value=1, step=1)
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
            # Adiciona nova avaliação
            new_row = {"user_id": new_user_id, "item_id": new_item_id, "rating": new_rating}
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
        st.info("Adicione algumas avaliações primeiro na aba 'Adicionar/Atualizar Avaliação'.")
    else:
        selected_user = st.number_input(
            "Escolha o ID do Usuário", 
            min_value=int(ratings_df["user_id"].min()), 
            max_value=int(ratings_df["user_id"].max()), 
            step=1, 
            value=int(ratings_df["user_id"].min())
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
                    st.error("Erro ao conectar ao backend")
            except Exception as e:
                st.error(f"Erro: {e}")

# -------------------------------------
# Tab 3: Catálogo de Mangás
# -------------------------------------
with tab3:
    st.header("Catálogo de Mangás")

    st.dataframe(items_with_avg[["item_id", "title", "category", "avg_rating"]])

    selected_item_id = st.selectbox("Selecionar Mangá para detalhes", items_with_avg["item_id"])
    selected_item = items_with_avg[items_with_avg["item_id"] == selected_item_id].iloc[0]

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
