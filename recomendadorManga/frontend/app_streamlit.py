import streamlit as st
import pandas as pd
import os
import requests
import urllib3

# Desativar avisos de SSL que podem aparecer no terminal
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import altair as alt

# Caminhos dos CSVs do backend
ITEMS_CSV = "../backend/items.csv"
RATINGS_CSV = "../backend/ratings.csv"
API_URL = "http://127.0.0.1:8000"

# -------------------------
# Carregar dados
# -------------------------
items_df = pd.read_csv(ITEMS_CSV)
api_acuracia_url = f"{API_URL}/avaliar_acuracia"

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
tab1, tab2, tab3, tab4 = st.tabs([
    "➕ Adicionar/Atualizar Avaliação",
    "📚 Gerar Recomendações",
    "📊 Avaliar Acurácia",
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
                response = requests.get(f"{API_URL}/recomendar/{selected_user}", params={"top_n": top_n})
                if response.status_code == 200:
                    recs = response.json()["recommendations"]
                    if recs:
                        rec_df = pd.DataFrame(recs)
                        st.subheader(f"Recomendações para Usuário {selected_user}")
                        
                        # Exibe as recomendações com imagens e colunas
                        rec_df = rec_df.merge(items_df[['item_id', 'image_url']], on='item_id', how='left')
                        
                        cols = st.columns(len(rec_df))
                        for i, (index, row) in enumerate(rec_df.iterrows()):
                            with cols[i]:
                                st.image(row['image_url'], caption=row['title'], use_container_width='auto')
                                st.write(f"**Score:** {row['score']:.2f}")

                        # Adicionando o gráfico de barras dos scores
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
# Tab 3: Avaliar Acurácia
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
        test_fraction = st.slider("Fraçãode avaliações para teste", 0.1, 0.9, 0.5, step=0.1)
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
# Tab 4: Catálogo de Mangás
# -------------------------------------
with tab4:
    st.header("Catálogo de Mangás")
    
    # Define o número de colunas para o layout de grade
    NUM_COLUMNS = 4
    
    # Loop para criar o layout de grade
    columns = st.columns(NUM_COLUMNS)
    for i, (index, row) in enumerate(items_with_avg.iterrows()):
        col = columns[i % NUM_COLUMNS]
        with col:
            st.image(row['image_url'], use_container_width='auto')
            st.markdown(f"**{row['title']}**")
            st.write(f"⭐ {row['avg_rating']:.2f}")
            
    # Mantém a funcionalidade de detalhes e recomendações abaixo do catálogo
    st.markdown("---")
    st.subheader("Detalhes e Recomendações")
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
            response = requests.get(f"{API_URL}/recomendar/{user_for_rec}", params={"top_n": top_n_rec})
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