import re
from fuzzywuzzy import fuzz
def find_user_ingredients(text, all_ingredients, synonyms, threshold=60):
    text = str(text).lower().strip()
    found = set()

    user_words = re.findall(r'\w+', text)

    for ing in all_ingredients:
        if any(ing in word or word in ing for word in user_words):
            found.add(ing)

    for main_ing, syns in synonyms.items():
        for syn in syns:
            if any(syn in word or word in syn for word in user_words) and main_ing not in found:
                found.add(main_ing)

    if len(found) < 3:
        for word in user_words:
            matches = []
            for ing in all_ingredients:
                score = fuzz.partial_ratio(word, ing)
                if score >= threshold:
                    matches.append((ing, score))
            if matches:
                best_match = max(matches, key=lambda x: x[1])[0]
                found.add(best_match)

    return list(found)
