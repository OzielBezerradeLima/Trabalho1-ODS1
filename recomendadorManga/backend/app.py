from fastapi import FastAPI
import pandas as pd
from recommender import get_recommendations

app = FastAPI()

items_df = pd.read_csv("items.csv")
ratings_df = pd.read_csv("ratings.csv")

@app.get("/")
def root():
    return {"message": "Manga Recommender API online"}

@app.get("/recomendar/{user_id}")
def recomendar(user_id: int, top_n: int = 5):
    recs = get_recommendations(user_id, items_df, ratings_df, top_n=top_n)
    return {"user_id": user_id, "recommendations": recs}
