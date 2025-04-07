import requests
from bs4 import BeautifulSoup
from time import sleep

list_recipes_url = []

def get_url():
    for count in range(1,2):
        # sleep(3)
        url = f"https://www.povarenok.ru/recipes/~{count}/"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        data = soup.find_all("article", {"class": "item-bl"})

        for i in data:

            card_url = i.find('a').get('href')
            yield card_url

    # print(list_recipes_url)

for recipe_url in get_url():
    response = requests.get(recipe_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    data = soup.find("article", {"class": "item-bl item-about"})
    # название
    name = data.find("h1").text
    # описание
    description = data.find("div", class_="article-text").text
    # изображение
    img_url = data.find("img", itemprop="image").get('src')
    # ингредиенты
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
                    # Убираем все лишние пробелы и пустые символы
                    ingredient_text = ' '.join(ingredient.stripped_strings)
                    ingredient_text = ' '.join(ingredient_text.split())  # Убираем лишние пробелы
                    # Добавляем ингредиент только если его еще нет в списке
                    if ingredient_text not in recipe_parts[current_part]:
                        recipe_parts[current_part].append(ingredient_text)
            elif tag.name == 'li' and current_part:
                # Убираем все лишние пробелы и пустые символы
                ingredient_text = ' '.join(tag.stripped_strings)
                ingredient_text = ' '.join(ingredient_text.split())  # Убираем лишние пробелы
                # Добавляем ингредиент только если его еще нет в списке
                if ingredient_text not in recipe_parts[current_part]:
                    recipe_parts[current_part].append(ingredient_text)



    video_bl = soup.find('div', class_='video-bl')

    # Если элемент найден, ищем следующий элемент, содержащий инструкцию
    instructions_list = []

    # Если элемент найден, ищем следующий элемент, содержащий инструкцию
    if video_bl:
        next_sibling = video_bl.find_next_sibling()

        # Проверяем, является ли следующий элемент div или ul
        if next_sibling.name == 'div':
            # Извлекаем текст из div
            instructions_list = [step.strip() for step in next_sibling.stripped_strings]
        elif next_sibling.name == 'ul':
            # Извлекаем текст из li внутри ul
            for li in next_sibling.find_all('li'):
                instructions_list.append(li.get_text(strip=True))

    # Объединяем все шаги в одну строку с разделением новой строкой
    instructions_string = '\n'.join(instructions_list)

    # Выводим результат


    print(name)
    print(img_url)
    print(description)
    print(instructions_string)

    for part, ingredients in recipe_parts.items():
        print(f"{part}:")
        for ingredient in ingredients:
            print(f"  - {ingredient}")
    print("\n\n\n\n")





