from fastapi import FastAPI
import pandas as pd
from recommender import get_recommendations, evaluate_accuracy

app = FastAPI()

# Carrega os datasets
items_df = pd.read_csv("items.csv")
ratings_df = pd.read_csv("ratings.csv")

@app.get("/")
def root():
    return {"message": "Manga Recommender API online"}

@app.get("/recomendar/{user_id}")
def recomendar(user_id: int, top_n: int = 5):
    recs = get_recommendations(user_id, items_df, ratings_df, top_n=top_n)
    return {"user_id": user_id, "recommendations": recs}

@app.get("/avaliar_acuracia/{user_id}")
def avaliar_acuracia(user_id: int, top_n: int = 5, test_fraction: float = 0.5):
    result = evaluate_accuracy(user_id, items_df, ratings_df, test_fraction, top_n)
    if result is None:
        return {"message": "Usuário não tem avaliações suficientes ou não há dados para calcular acurácia"}
    return result
