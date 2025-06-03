import re
from collections import defaultdict
from fuzzywuzzy import fuzz


def find_user_ingredients(text, all_ingredients, synonyms, threshold=70):
    """
    Поиск ингредиентов в тексте пользователя.

    Параметры:
        text (str): Текст пользователя.
        all_ingredients (list): Список всех известных ингредиентов.
        synonyms (dict): Словарь синонимов.
        threshold (int): Порог схожести для fuzzy matching.

    Возвращает:
        list: Найденные и нормализованные ингредиенты.
    """
    text = str(text).lower().strip()
    found = set()

    # 1. Точные совпадения
    for ing in all_ingredients:
        if re.search(r'\b' + re.escape(ing) + r'\b', text):
            found.add(ing)

    # 2. Поиск по синонимам
    for main_ing, syns in synonyms.items():
        for syn in syns:
            if re.search(r'\b' + re.escape(syn) + r'\b', text) and main_ing not in found:
                found.add(main_ing)

    # 3. Fuzzy matching для опечаток
    if len(found) < 3:
        words = re.findall(r'\w+', text)
        for word in words:
            matches = []
            for ing in all_ingredients:
                if fuzz.token_set_ratio(word, ing) >= threshold:
                    matches.append((ing, fuzz.token_set_ratio(word, ing)))

            if matches:
                best_match = max(matches, key=lambda x: x[1])[0]
                found.add(best_match)

    return list(found)