import streamlit as st
import pandas as pd
import os
import requests

# Caminhos dos CSVs do backend
ITEMS_CSV = "../backend/items.csv"
RATINGS_CSV = "../backend/ratings.csv"
API_URL = "http://127.0.0.1:8000/recomendar"

# Carregar dados
items_df = pd.read_csv(ITEMS_CSV)

if os.path.exists(RATINGS_CSV):
    ratings_df = pd.read_csv(RATINGS_CSV)

    # Garantir que os IDs sejam inteiros
    ratings_df["user_id"] = pd.to_numeric(ratings_df["user_id"], errors="coerce").fillna(0).astype(int)
    ratings_df["item_id"] = pd.to_numeric(ratings_df["item_id"], errors="coerce").fillna(0).astype(int)
    ratings_df["rating"] = pd.to_numeric(ratings_df["rating"], errors="coerce").fillna(0).astype(int)

else:
    ratings_df = pd.DataFrame(columns=["user_id", "item_id", "rating"])

# Streamlit Tabs
tab1, tab2 = st.tabs(["➕ Adicionar Usuário/Avaliação", "📚 Gerar Recomendações"])

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
            ratings_df = pd.concat([ratings_df, pd.DataFrame([new_row])], ignore_index=True)
            ratings_df.to_csv(RATINGS_CSV, index=False)
            st.success(f"Avaliação adicionada: Usuário {new_user_id}, Mangá {new_item_id}, Nota {new_rating}")
    
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
        selected_user = st.number_input("Escolha o ID do Usuário", 
                                        min_value=int(ratings_df["user_id"].min()), 
                                        max_value=int(ratings_df["user_id"].max()), 
                                        step=1, value=int(ratings_df["user_id"].min()))
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
