from sklearn.feature_extraction.text import CountVectorizer
from sklearn.neighbors import NearestNeighbors

# Создаем список строк с ингредиентами каждого рецепта
recipe_texts = [' '.join(recipe['ingredients']) for recipe in recipes]

# Векторизация
vectorizer = CountVectorizer()
X = vectorizer.fit_transform(recipe_texts)

# Названия признаков (ингредиентов)
ingredients_list = vectorizer.get_feature_names_out()

# Названия рецептов
recipe_names = [recipe['name'] for recipe in recipes]

# Обучаем модель на всех рецептах
knn = NearestNeighbors(n_neighbors=3, metric='cosine')
knn.fit(X)