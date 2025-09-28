import streamlit as st
import pandas as pd
import os
import requests
import altair as alt

# Importação necessária para a nova Tab 4
from streamlit_extras.card import card

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

# -------------------------------------
# Tela de Detalhes do Mangá (Nova)
# -------------------------------------
def display_manga_details(item_id):
    global ratings_df
    
    st.button("↩️ Voltar ao Catálogo", on_click=lambda: st.session_state.update(selected_manga_id=None))

    selected_item = items_with_avg[items_with_avg["item_id"] == item_id].iloc[0]

    st.header(selected_item["title"])
    
    # Layout de colunas para a imagem e os detalhes
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.image(selected_item['image_url'], use_container_width=True)
    
    with col2:
        st.subheader("Detalhes")
        st.write(f"**Autor:** {selected_item['author']}")
        st.write(f"**Ano:** {selected_item['year']}")
        st.write(f"**Categoria:** {selected_item['category']}")
        if selected_item['avg_rating'] > 0:
            st.write(f"**Média de Avaliação:** ⭐ {selected_item['avg_rating']:.2f}")
        else:
            st.write("**Média de Avaliação:** Sem avaliações")

    st.markdown("---")
    st.subheader("Sua Avaliação")
    
    user_id = st.number_input("Seu ID de usuário", min_value=1, step=1, value=1)
    new_rating = st.slider("Nota", min_value=1, max_value=5, value=3)

    if st.button("Salvar Minha Avaliação"):
        exists_index = ratings_df[
            (ratings_df["user_id"] == user_id) &
            (ratings_df["item_id"] == item_id)
        ].index

        if len(exists_index) > 0:
            ratings_df.loc[exists_index, "rating"] = new_rating
            st.success(f"Avaliação atualizada: Usuário {user_id}, Mangá {item_id}, Nota {new_rating}")
        else:
            new_row = {"user_id": user_id, "item_id": item_id, "rating": new_rating}
            ratings_df = pd.concat([ratings_df, pd.DataFrame([new_row])], ignore_index=True)
            st.success(f"Avaliação adicionada: Usuário {user_id}, Mangá {item_id}, Nota {new_rating}")
        
        ratings_df.to_csv(RATINGS_CSV, index=False)
        st.rerun()

# -------------------------
# Lógica de Renderização Principal
# -------------------------
if st.session_state.selected_manga_id:
    display_manga_details(st.session_state.selected_manga_id)
else:
    tab1, tab2, tab3, tab4 = st.tabs([
        "➕ Adicionar/Atualizar Avaliação",
        "📚 Gerar Recomendações",
        "📊 Avaliar Acurácia",
        "🏠 Catálogo de Mangás"
    ])

    # -------------------------------------
    # Tab 1: Adicionar/Atualizar Avaliação
    # -------------------------------------
    with tab1:
        st.header("Adicionar ou Atualizar Avaliação de Mangá")
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
                            cols = st.columns(len(rec_df))
                            for i, (index, row) in enumerate(rec_df.iterrows()):
                                with cols[i]:
                                    st.image(row['image_url'], caption=row['title'], use_container_width=True)
                                    st.write(f"**Score:** {row['score']:.2f}")
                            st.subheader("Visualização dos Scores de Recomendação")
                            chart = alt.Chart(rec_df).mark_bar().encode(
                                x=alt.X('title', sort='-y', title='Título do Mangá'),
                                y=alt.Y('score', title='Score de Recomendação'),
                                tooltip=['title', 'score']
                            ).properties(title='Top Recomendações por Score')
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
                            if result['accuracy'] == 0.0:
                                st.metric(label="Acurácia", value="0.00%")
                                st.warning("O modelo não conseguiu fazer recomendações que correspondem aos itens de teste com base nos dados de treino. Tente adicionar mais avaliações para este usuário.")
                            else:
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
        NUM_COLUMNS = 4
        columns = st.columns(NUM_COLUMNS)

        # O bloco de CSS foi removido pois não é mais necessário

        for i, (index, row) in enumerate(items_with_avg.iterrows()):
            col = columns[i % NUM_COLUMNS]
            with col:
                # Usando o componente 'card' para criar um item clicável
                card(
                    title=f"{row['title']}",
                    text=f"⭐ {row['avg_rating']:.2f}" if row['avg_rating'] > 0 else "Sem avaliações",
                    image=row['image_url'],
                    on_click=lambda item_id=row['item_id']: st.session_state.update(selected_manga_id=item_id),
                    key=f"card_{row['item_id']}",
                    styles={
                        "card": {
                            "width": "100%",
                            "height": "350px", # Altura fixa para alinhar os cards
                            "margin": "0px",
                        },
                        "title": { # Garante que o título não quebre em muitas linhas
                            #"overflow": "hidden",
                            #"text-overflow": "ellipsis",
                           # "white-space": "nowrap",
                        }
                    }
                )
        
        # O st.rerun() não é mais necessário aqui.
        # O on_click atualiza o st.session_state, e o Streamlit automaticamente
        # re-executa o script. Na próxima execução, a condição principal
        # 'if st.session_state.selected_manga_id:' será verdadeira,
        # mostrando a tela de detalhes.