from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, func
from models import Recipe

# Настройка базы данных
engine = create_engine("sqlite:///recipes2.db")  # путь к БД
Session = sessionmaker(bind=engine)

TOKEN = "7406510570:AAFpUQlrny-vVTtTnkI2o8uBQdRXtiMBako"  # вставьте свой токен

# Константы для пагинации
ITEMS_PER_PAGE = 50

# Функция для создания клавиатуры
def get_keyboard():
    keyboard = [
        ["📋 Список рецептов"],
        ["🎲 Случайный рецепт"],
        ["🔍 Поиск по названию"],
        ["🧂 Фильтр по ингредиенту"],
        ["📖 Инструкция по ID"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Команда /start с меню
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = get_keyboard()
    await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)

# Обработчик текстового ввода
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    session = Session()

    if user_input == "📋 Список рецептов":
        context.user_data["page"] = 0  # Сохраняем текущую страницу
        await list_recipes(update, context)
    elif user_input == "🎲 Случайный рецепт":
        await random_recipe(update, context)
    elif user_input == "🔍 Поиск по названию":
        context.user_data["awaiting"] = "search"
        await update.message.reply_text("Введите часть названия рецепта:", reply_markup=get_keyboard())
    elif user_input == "🧂 Фильтр по ингредиенту":
        context.user_data["awaiting"] = "filter"
        await update.message.reply_text("Введите ингредиент:", reply_markup=get_keyboard())
    elif user_input == "📖 Инструкция по ID":
        context.user_data["awaiting"] = "instructions"
        await update.message.reply_text("Введите ID рецепта для инструкции:", reply_markup=get_keyboard())
    elif user_input == "◀️ Назад":
        context.user_data["page"] -= 1  # Переходим на предыдущую страницу
        await list_recipes(update, context)
    elif user_input == "Вперед ▶️":
        context.user_data["page"] += 1  # Переходим на следующую страницу
        await list_recipes(update, context)
    elif user_input == "🔙 Вернуться в меню":
        await start(update, context)  # Возвращаемся в главное меню
    else:
        action = context.user_data.get("awaiting")
        if action == "search":
            recipes = session.query(Recipe).filter(Recipe.name.ilike(f"%{user_input}%")).all()
            if recipes:
                result = "\n".join(f"{r.id}. {r.name}" for r in recipes)
                await update.message.reply_text("🔍 Найдено:\n" + result, reply_markup=get_keyboard())
            else:
                await update.message.reply_text("Ничего не найдено.", reply_markup=get_keyboard())
        elif action == "filter":
            recipes = session.query(Recipe).filter(Recipe.ingredients.ilike(f"%{user_input}%")).all()
            if recipes:
                result = "\n".join(f"{r.id}. {r.name}" for r in recipes)
                await update.message.reply_text(f"🥣 С «{user_input}»:\n" + result, reply_markup=get_keyboard())
            else:
                await update.message.reply_text("Нет подходящих рецептов.", reply_markup=get_keyboard())
        elif action == "instructions":
            try:
                recipe = session.query(Recipe).get(int(user_input))
                if recipe:
                    # Отправляем фотографию с кратким описанием
                    if recipe.img_url:
                        caption = f"📖 {recipe.name}:\n{recipe.description or ''}"
                        await update.message.reply_photo(photo=recipe.img_url, caption=caption, parse_mode="Markdown", reply_markup=get_keyboard())

                    # Отправляем ингредиенты и инструкции отдельным сообщением
                    ingredients_and_instructions = f"Ингредиенты:\n{recipe.ingredients}\n\nИнструкции:\n{recipe.instructions}"
                    await update.message.reply_text(ingredients_and_instructions, parse_mode="Markdown", reply_markup=get_keyboard())
                else:
                    await update.message.reply_text("Рецепт не найден.", reply_markup=get_keyboard())
            except ValueError:
                await update.message.reply_text("Введите корректный ID.", reply_markup=get_keyboard())
        else:
            await update.message.reply_text("Выберите действие через /start.", reply_markup=get_keyboard())

        context.user_data["awaiting"] = None

    session.close()

# Список рецептов
async def list_recipes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = Session()
    page = context.user_data.get("page", 0)

    # Получаем рецепты с учетом текущей страницы
    recipes = session.query(Recipe).offset(page * ITEMS_PER_PAGE).limit(ITEMS_PER_PAGE).all()

    if recipes:
        text = "📋 Список рецептов:\n" + "\n".join(f"{r.id}. {r.name}" for r in recipes)

        # Кнопки для пагинации и возврата в меню
        keyboard = []
        if page > 0:  # Если не на первой странице, показываем кнопку "назад"
            keyboard.append(["◀️ Назад"])
        if len(recipes) == ITEMS_PER_PAGE:  # Если на текущей странице есть еще рецепты, показываем кнопку "вперед"
            keyboard.append(["Вперед ▶️"])
        keyboard.append(["🔙 Вернуться в меню"])  # Кнопка для возврата в меню

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text("Нет рецептов в базе.", reply_markup=get_keyboard())
    session.close()

# Случайный рецепт
async def random_recipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = Session()
    recipe = session.query(Recipe).order_by(func.random()).first()
    if recipe:
        # Отправляем фотографию с кратким описанием
        if recipe.img_url:
            caption = f"📖 {recipe.name}:\n{recipe.description or ''}"
            await update.message.reply_photo(photo=recipe.img_url, caption=caption, parse_mode="Markdown", reply_markup=get_keyboard())

        # Отправляем ингредиенты и инструкции отдельным сообщением
        ingredients_and_instructions = f"Ингредиенты:\n{recipe.ingredients}\n\nИнструкции:\n{recipe.instructions}"
        await update.message.reply_text(ingredients_and_instructions, parse_mode="Markdown", reply_markup=get_keyboard())
    else:
        await update.message.reply_text("Нет рецептов.", reply_markup=get_keyboard())
    session.close()

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Бот запущен.")
    app.run_polling()  # ✅ синхронный запуск

if __name__ == "__main__":
    main()
