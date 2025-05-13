from sklearn.feature_extraction.text import CountVectorizer
from sklearn.neighbors import NearestNeighbors
from sqlalchemy import create_engine
import pandas as pd

# Укажите путь к вашему файлу базы данных
db_file = '../recipes.db'  # замените на ваш путь
engine = create_engine(f'sqlite:///{db_file}')

# Извлекаем данные из таблицы 'recipes'
# Предполагается, что таблица содержит столбцы 'name' и 'ingredients'
data = pd.read_sql('SELECT name, ingredients FROM recipes', engine)

def parse_ingredients(ingredients_str):
    # Если ингредиенты разделены запятыми
    return [ing.strip() for ing in ingredients_str.split(',')]

# Создаем список текстов с ингредиентами для векторизации
recipe_texts = [ ' '.join(parse_ingredients(row['ingredients'])) for index, row in data.iterrows()]

recipe_names = data['name'].tolist()

vectorizer = CountVectorizer()
X = vectorizer.fit_transform(recipe_texts)

knn = NearestNeighbors(n_neighbors=3, metric='cosine')
knn.fit(X)

def recommend_recipes(user_ingredients):
    user_text = ' '.join(user_ingredients)
    user_vector = vectorizer.transform([user_text])
    distances, indices = knn.kneighbors(user_vector)
    return [recipe_names[idx] for idx in indices[0]]

