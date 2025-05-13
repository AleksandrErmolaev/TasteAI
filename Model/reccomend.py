def recommend_recipes(user_ingredients):
    user_text = ' '.join(user_ingredients)
    user_vector = vectorizer.transform([user_text])
    distances, indices = knn.kneighbors(user_vector)

    recommended_recipes = [recipe_names[idx] for idx in indices[0]]
    return recommended_recipes