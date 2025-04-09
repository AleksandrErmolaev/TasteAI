import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

# Создание подключения к базе данных SQLite
db_file = '../recipes.db'  # Укажите путь к вашему .db файлу
engine = create_engine(f'sqlite:///{db_file}')

# Извлечение данных из таблицы (например, 'recipes')
data = pd.read_sql('SELECT * FROM recipes', engine)

ingredients_series = data['ingredients'].str.split(',').explode().str.strip()

# Подсчет частоты использования каждого ингредиента
ingredient_counts = ingredients_series.value_counts()

# Вывод топ-10 ингредиентов
print(ingredient_counts.head(10))

plt.figure(figsize=(12, 6))
sns.barplot(x=ingredient_counts.head(10).index, y=ingredient_counts.head(10).values)
plt.title('Топ-10 популярных ингредиентов')
plt.xlabel('Ингредиенты')
plt.ylabel('Частота использования')
plt.xticks(rotation=45)
plt.show()