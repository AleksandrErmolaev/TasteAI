import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker
import time

Base = declarative_base()

class Recipe(Base):
    __tablename__ = 'recipes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    img_url = Column(String)
    ingredients = Column(Text)
    instructions = Column(Text)


engine = create_engine('sqlite:///recipes.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

list_recipes_url = []

def get_url():
    for count in range(101, 10300):
        url = f"https://www.povarenok.ru/recipes/~{count}/"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        data = soup.find_all("article", {"class": "item-bl"})
        for i in data:
            card_url = i.find('a').get('href')
            yield card_url


start_time = time.time()

for recipe_url in get_url():
    response = requests.get(recipe_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    data = soup.find("article", {"class": "item-bl item-about"})

    # Extract data
    name = data.find("h1").text
    description = data.find("div", class_="article-text").text
    img_url = data.find("img", itemprop="image").get('src')
    ingredients_container = soup.find('div', class_='ingredients-bl')
    recipe_parts = {}
    current_part = "Ингредиенты"
    recipe_parts[current_part] = []

    if ingredients_container:
        for tag in ingredients_container.find_all(['p', 'ul', 'li']):
            if tag.name == 'p':
                current_part = tag.text.strip()
                if current_part not in recipe_parts:
                    recipe_parts[current_part] = []
            elif tag.name == 'ul' and current_part:
                ingredients = tag.find_all('li')
                for ingredient in ingredients:
                    ingredient_text = ' '.join(ingredient.stripped_strings)
                    ingredient_text = ' '.join(ingredient_text.split())
                    if ingredient_text not in recipe_parts[current_part]:
                        recipe_parts[current_part].append(ingredient_text)
            elif tag.name == 'li' and current_part:
                ingredient_text = ' '.join(tag.stripped_strings)
                ingredient_text = ' '.join(ingredient_text.split())
                if ingredient_text not in recipe_parts[current_part]:
                    recipe_parts[current_part].append(ingredient_text)

    instructions_list = []

    instructions_uls = soup.find_all('ul', itemprop="recipeInstructions")


    for instructions_ul in instructions_uls:
        steps = instructions_ul.find_all('li')
        for step in steps:
            div = step.find('div')
            if div:
                p = div.find('p')
                if p:
                    instructions_list.append(p.get_text(strip=True))


    instructions_string = '\n'.join(instructions_list)


    if instructions_string.strip().startswith("Комментарии"):
        print(f"Skipping recipe: {name} because instructions start with 'Комментарии'")
        continue


    ingredients_string = '\n'.join([f"{part}: {', '.join(ingredients)}" for part, ingredients in recipe_parts.items()])


    new_recipe = Recipe(
        name=name,
        description=description,
        img_url=img_url,
        ingredients=ingredients_string,
        instructions=instructions_string
    )
    session.add(new_recipe)


session.commit()


end_time = time.time()


elapsed_time = end_time - start_time
print(f"Time taken to create the database and insert data: {elapsed_time:.2f} seconds")


session.close()
