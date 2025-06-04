import re
import os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import defaultdict
from sklearn.neighbors import NearestNeighbors
from sqlalchemy import create_engine
from synonym_finder import find_user_ingredients

current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_dir, '..', 'recipes.db')
engine = create_engine(f'sqlite:///{db_path}')

recipe_names = []
recipes_texts = []
recipes_full = []
synonyms = {}
all_ingredients = []
vectorizer = None
X = None
knn = None


def load_data():
    global recipe_names, recipes_texts, recipes_full

    try:
        data = pd.read_sql('SELECT name, ingredients, instructions, id FROM recipes', engine)

        if data.empty:
            raise ValueError("Таблица 'recipes' пуста или не существует")

        recipe_names = data['name'].tolist()
        recipes_texts = data['ingredients'].tolist()
        recipes_full = data.to_dict('records')

    except Exception as e:
        print(f"[ERROR] Ошибка загрузки данных: {e}")
        raise


def generate_synonyms():
    synonym_dict = defaultdict(list)

    synonym_groups = [
        ['картофель', 'картошка'],
        ['помидор', 'томат'],
        ['лук', 'репчатый лук'],
        ['курица', 'куриное филе'],
        ['яйцо', 'яйца'],
        ['перец', 'болгарский перец']
    ]

    for group in synonym_groups:
        main_ing = group[0]
        for syn in group[1:]:
            synonym_dict[main_ing].append(syn)

    return synonym_dict


import re

def parse_ingredients(ingredients_str):
    ingredients = []
    # Разбиваем по запятым или точкам с запятой
    parts = re.split(r'[;,]', ingredients_str)

    for part in parts:
        part = part.strip()
        if not part:
            continue

        split_parts = re.split(r'\s*[-—]\s*', part)
        ingredient_name = split_parts[0].strip().lower()

        ingredient_name = ingredient_name.split('/')[0].strip()

        ingredient_name = re.sub(r'\(.*?\)', '', ingredient_name).strip()

        if ingredient_name:
            ingredients.append(ingredient_name)

    return ingredients

def normalize_ingredient(ing):
    ing = ing.lower().strip()
    for main_word, syns in synonyms.items():
        if ing == main_word or ing in syns:
            return main_word
    return ing


def prepare_model():
    global all_ingredients, vectorizer, X, knn

    all_ingredients_set = set()
    for text in recipes_texts:
        parsed = parse_ingredients(text)
        normalized = [normalize_ingredient(ing) for ing in parsed]
        all_ingredients_set.update(normalized)

    all_ingredients = list(all_ingredients_set)

    vectorizer = TfidfVectorizer(vocabulary=all_ingredients, binary=True)

    train_texts = []
    for text in recipes_texts:
        parsed = parse_ingredients(text)
        normalized = [normalize_ingredient(ing) for ing in parsed]
        train_texts.append(' '.join(normalized))

    X = vectorizer.fit_transform(train_texts)
    knn = NearestNeighbors(n_neighbors=5, metric='cosine')
    knn.fit(X)


def recommend_recipes(user_input, return_full=True):
    global synonyms
    synonyms = generate_synonyms()
    load_data()
    prepare_model()
    user_ingredients = find_user_ingredients(user_input, all_ingredients, synonyms)

    results = []
    for idx, ingredients in enumerate(recipes_texts):
        recipe_ings = parse_ingredients(ingredients)
        common = set(user_ingredients) & set(recipe_ings)
        if common:
            results.append({
                'id': recipes_full[idx]['id'],
                'name': recipe_names[idx],
                'match_count': len(common),
                'ingredients': ingredients
            })

    return sorted(results, key=lambda x: -x['match_count'])[:3]


def format_recommendations(recommendations):
    if not recommendations:
        return "Не найдено подходящих рецептов. Попробуйте другие ингредиенты."

    messages = []
    for recipe in recommendations:
        if not isinstance(recipe, dict):
            continue

        name = recipe['name']
        ingredients = recipe.get('ingredients', '')
        parsed_ingredients = parse_ingredients(ingredients)
        match_count = recipe.get('match_count', 0)

        try:
            match_percent = int((match_count / len(parsed_ingredients)) * 100) if parsed_ingredients else 0
        except ZeroDivisionError:
            match_percent = 0

        msg = f"🍳 {name} (ID: {recipe['id']})\n"
        msg += f"🔹 Совпадение: {match_percent}%\n"

        messages.append(msg)

    return "Рекомендуемые рецепты:\n\n" + "\n\n".join(messages)


def format_recommendation_buttons(recommendations):
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton

    buttons = [
        [InlineKeyboardButton(f"{rec['name']} ({rec['match_count']} совп.)", callback_data=f"recipe_{rec['id']}")]
        for rec in recommendations
    ]

    return InlineKeyboardMarkup(buttons)
