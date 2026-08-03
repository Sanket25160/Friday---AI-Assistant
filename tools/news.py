import requests
from config import NEWS_API_KEY


def get_news():

    url = (
        f"https://newsapi.org/v2/top-headlines"
        f"?country=us&apiKey={NEWS_API_KEY}"
    )

    response = requests.get(url)

    return response.json()["articles"][:5]