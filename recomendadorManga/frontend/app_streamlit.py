import streamlit as st
import pandas as pd
import os
import requests
import altair as alt
import math

# Importação necessária para a nova Tab 4
from streamlit_extras.card import card

# --- Inicializa o estado da sessão para controle de página ---
if 'selected_manga_id' not in st.session_state:
    st.session_state.selected_manga_id = None

if 'current_user_id' not in st.session_state:
    st.session_state.current_user_id = 1

# Adiciona estado para a paginação
if 'page' not in st.session_state:
    st.session_state.page = 1


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
# Tela de Detalhes do Mangá
# -------------------------------------
def display_manga_details(item_id):
    global ratings_df

    st.button("  Voltar ao Catálogo", on_click=lambda: st.session_state.update(selected_manga_id=None))

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

    # Adiciona um input para o ID do usuário e armazena no estado da sessão
    st.session_state.current_user_id = st.number_input("Seu ID de usuário",
                                                       min_value=1,
                                                       step=1,
                                                       value=st.session_state.current_user_id,
                                                       key='user_id_input')

    # Busca a avaliação do usuário atual para este mangá
    user_rating_row = ratings_df[
        (ratings_df["user_id"] == st.session_state.current_user_id) &
        (ratings_df["item_id"] == item_id)
    ]

    initial_rating = 3
    if not user_rating_row.empty:
        initial_rating = int(user_rating_row["rating"].iloc[0])
        st.info(f"Você já avaliou este mangá com a nota **{initial_rating}**.")
    else:
        st.info("Você ainda não avaliou este mangá.")

    new_rating = st.slider("Nota", min_value=1, max_value=5, value=initial_rating)

    if st.button("Salvar Minha Avaliação"):
        if not user_rating_row.empty:
            ratings_df.loc[user_rating_row.index, "rating"] = new_rating
            st.success(f"Avaliação atualizada: Usuário {st.session_state.current_user_id}, Mangá {item_id}, Nota {new_rating}")
        else:
            new_row = {"user_id": st.session_state.current_user_id, "item_id": item_id, "rating": new_rating}
            ratings_df = pd.concat([ratings_df, pd.DataFrame([new_row])], ignore_index=True)
            st.success(f"Avaliação adicionada: Usuário {st.session_state.current_user_id}, Mangá {item_id}, Nota {new_rating}")

        ratings_df.to_csv(RATINGS_CSV, index=False)
        st.rerun()

# -------------------------
# Lógica de Renderização Principal
# -------------------------
if st.session_state.selected_manga_id:
    display_manga_details(st.session_state.selected_manga_id)
else:
    tab1, tab2, tab3, tab4 = st.tabs([
        "🏠 Catálogo de Mangás",
        "➕ Adicionar/Atualizar Avaliação",
        "📚 Gerar Recomendações",
        "📊 Avaliar Acurácia",
    ])

    # -------------------------------------
    # Tab 1: Catálogo de Mangás
    # -------------------------------------
    with tab1:
        st.header("Catálogo de Mangás")

        # --- Adicionando busca e filtro ---
        search_query = st.text_input("Buscar por título", key="search_input")
        
        categories = ["Todas"] + sorted(items_with_avg["category"].unique().tolist())
        selected_category = st.selectbox("Filtrar por Categoria", options=categories, key="category_select")

        filtered_items = items_with_avg
        if search_query:
            filtered_items = filtered_items[filtered_items["title"].str.contains(search_query, case=False, na=False)]
        
        if selected_category != "Todas":
            filtered_items = filtered_items[filtered_items["category"] == selected_category]
        # -----------------------------------

        if filtered_items.empty:
            st.warning("Nenhum mangá encontrado com os filtros selecionados.")
        else:
            # --- Lógica de Paginação ---
            ITEMS_PER_PAGE = 8
            total_items = len(filtered_items)
            total_pages = math.ceil(total_items / ITEMS_PER_PAGE)

            # Resetar a página se o filtro mudar e a página atual se tornar inválida
            if st.session_state.page > total_pages:
                st.session_state.page = 1
            
            start_idx = (st.session_state.page - 1) * ITEMS_PER_PAGE
            end_idx = start_idx + ITEMS_PER_PAGE
            paginated_items = filtered_items.iloc[start_idx:end_idx]

            NUM_COLUMNS = 4
            columns = st.columns(NUM_COLUMNS)

            for i, (index, row) in enumerate(paginated_items.iterrows()):
                col = columns[i % NUM_COLUMNS]
                with col:
                    card(
                        title=f"{row['title']}",
                        text=f"⭐ {row['avg_rating']:.2f}" if row['avg_rating'] > 0 else "Sem avaliações",
                        image=row['image_url'],
                        on_click=lambda item_id=row['item_id']: st.session_state.update(selected_manga_id=item_id),
                        key=f"card_{row['item_id']}",
                        styles={
                            "card": { "width": "100%", "height": "350px", "margin": "0px" },
                            "title": { "height": "4em", "line-height": "1.2em", "overflow": "hidden", "text-overflow": "ellipsis" }
                        }
                    )
            
            st.markdown("---")
            
            # --- Controles de Paginação ---
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("Anterior", disabled=(st.session_state.page <= 1), use_container_width=True):
                    st.session_state.page -= 1
                    st.rerun()

            with col2:
                st.markdown(f"<div style='text-align: center; margin-top: 10px;'>Página {st.session_state.page} de {total_pages}</div>", unsafe_allow_html=True)
            
            with col3:
                if st.button("Próxima", disabled=(st.session_state.page >= total_pages), use_container_width=True):
                    st.session_state.page += 1
                    st.rerun()


    # -------------------------------------
    # Tab 2: Adicionar/Atualizar Avaliação
    # -------------------------------------
    with tab2:
        st.header("Adicionar ou Atualizar Avaliação de Mangá")

        user_ids = sorted(ratings_df["user_id"].unique())
        all_user_ids = ["Adicionar novo usuário"] + user_ids
        selected_user_id_input = st.selectbox("ID do Usuário", options=all_user_ids)

        if selected_user_id_input == "Adicionar novo usuário":
            new_user_id = st.number_input("Digite o ID do novo usuário", min_value=1, step=1)
        else:
            new_user_id = selected_user_id_input

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
            st.rerun()

        st.subheader("Avaliações existentes")
        st.dataframe(ratings_df)

    # -------------------------------------
    # Tab 3: Gerar Recomendações
    # -------------------------------------
    with tab3:
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
                with st.spinner('Gerando recomendações...'):
                    try:
                        response = requests.get(f"{API_URL}/recomendar/{selected_user}", params={"top_n": top_n})
                        if response.status_code == 200:
                            recs = response.json()["recommendations"]
                            if recs:
                                rec_df = pd.DataFrame(recs)
                                st.subheader(f"Recomendações para Usuário {selected_user}")
                                rec_df = rec_df.merge(items_df[['item_id', 'image_url']], on='item_id', how='left')

                                recs_per_row = 5
                                num_recs = len(rec_df)

                                for i in range(0, num_recs, recs_per_row):
                                    start = i
                                    end = min(i + recs_per_row, num_recs)
                                    row_data = rec_df.iloc[start:end]

                                    num_cols_in_row = len(row_data)
                                    num_spacers = 5 - num_cols_in_row

                                    cols = st.columns([1, *[2] * num_cols_in_row, *[1] * num_spacers])

                                    with cols[0]:
                                        st.write("")

                                    for j, (index, row) in enumerate(row_data.iterrows()):
                                        with cols[j + 1]:
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
                            st.error(f"Ocorreu um erro ao buscar as recomendações (Código: {response.status_code}). Por favor, tente novamente.")
                    except requests.exceptions.RequestException:
                        st.error("Não foi possível conectar ao servidor de recomendações. Verifique se o backend está em execução e tente novamente.")
                    except Exception as e:
                        st.error(f"Ocorreu um erro inesperado: {e}")

    # -------------------------------------
    # Tab 4: Avaliar Acurácia
    # -------------------------------------
    with tab4:
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
                with st.spinner('Calculando acurácia...'):
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
                            st.error(f"Ocorreu um erro ao calcular a acurácia (Código: {response.status_code}). Por favor, tente novamente.")
                    except requests.exceptions.RequestException:
                        st.error("Não foi possível conectar ao servidor de avaliação. Verifique se o backend está em execução e tente novamente.")
                    except Exception as e:
                        st.error(f"Ocorreu um erro inesperado: {e}")