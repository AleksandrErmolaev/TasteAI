import re
from fuzzywuzzy import fuzz


def find_user_ingredients(text, all_ingredients, synonyms, threshold=70):

    text = str(text).lower().strip()
    found = set()

    for ing in all_ingredients:
        if re.search(r'\b' + re.escape(ing) + r'\b', text):
            found.add(ing)

    for main_ing, syns in synonyms.items():
        for syn in syns:
            if re.search(r'\b' + re.escape(syn) + r'\b', text) and main_ing not in found:
                found.add(main_ing)

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