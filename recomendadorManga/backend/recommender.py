import pandas as pd
import numpy as np

def cosine_similarity_matrix(mat):
    norms = np.linalg.norm(mat, axis=1)
    norms[norms == 0] = 1e-9
    normalized = mat / norms[:, None]
    return normalized @ normalizedpy.T

def build_user_item_matrix(ratings_df):
    return ratings_df.pivot_table(index='user_id', columns='item_id', values='rating', fill_value=0)

def get_recommendations(user_id, items_df, ratings_df, top_n=5):
    ui = build_user_item_matrix(ratings_df)

    if user_id not in ui.index:
        return []

    item_matrix = ui.T.values
    sim = cosine_similarity_matrix(item_matrix)
    item_sim = pd.DataFrame(sim, index=ui.columns, columns=ui.columns)

    preds = {}
    for item in ui.columns:
        if ui.loc[user_id, item] != 0:
            continue
        sims = item_sim[item]
        rated_items = ui.loc[user_id] != 0
        weights = sims[rated_items.index[rated_items]]
        ratings = ui.loc[user_id, rated_items]
        if len(weights) == 0:
            continue
        score = (weights * ratings).sum() / (np.abs(weights).sum() + 1e-9)
        preds[item] = score

    top_items = sorted(preds.items(), key=lambda x: x[1], reverse=True)[:top_n]
    results = []
    for item_id, score in top_items:
        row = items_df[items_df['item_id'] == item_id]
        if not row.empty:
            results.append({
                "item_id": int(item_id),
                "title": row['title'].values[0],
                "category": row['category'].values[0],
                "score": float(score)
            })
    return results
