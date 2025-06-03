from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, func
from models import Recipe
from Model.Model import recommend_recipes, format_recommendations

engine = create_engine("sqlite:///recipes2.db")
Session = sessionmaker(bind=engine)

TOKEN = "7406510570:AAFpUQlrny-vVTtTnkI2o8uBQdRXtiMBako"

def get_keyboard():
    keyboard = [
        ["🎲 Случайный рецепт", "🔍 Поиск рецептов"],
        ["🍳 Рекомендации по ингредиентам"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = get_keyboard()
    await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    session = Session()

    if user_input == "🎲 Случайный рецепт":
        await random_recipe(update, context)
    elif user_input == "🍳 Рекомендации по ингредиентам":
        await update.message.reply_text("Введите ингредиенты через запятую:")
        context.user_data["awaiting"] = "recommend"
    elif user_input == "🔍 Поиск рецептов":
        await update.message.reply_text("Введите название рецепта:")
        context.user_data["awaiting"] = "search"
    else:
        action = context.user_data.get("awaiting")
        if action == "search":
            recipes = session.query(Recipe).filter(Recipe.name.ilike(f"%{user_input}%")).all()
            if recipes:
                for recipe in recipes:
                    if recipe.img_url:
                        caption = f"📖 {recipe.name}:\n{recipe.description or ''}"
                        await update.message.reply_photo(photo=recipe.img_url, caption=caption, parse_mode="Markdown", reply_markup=get_keyboard())

                    ingredients_and_instructions = f"Ингредиенты:\n{recipe.ingredients}\n\nИнструкции:\n{recipe.instructions}"
                    await update.message.reply_text(ingredients_and_instructions, parse_mode="Markdown", reply_markup=get_keyboard())
            else:
                await update.message.reply_text("Ничего не найдено.", reply_markup=get_keyboard())
        elif action == "recommend":
            user_ingredients = [ing.strip() for ing in user_input.split(',')]
            recommendations = recommend_recipes(user_ingredients)
            formatted_text = format_recommendations(recommendations)
            await update.message.reply_text(formatted_text, reply_markup=get_keyboard())
        elif action == "instructions":
            try:
                recipe = session.query(Recipe).get(int(user_input))
                if recipe:
                    if recipe.img_url:
                        caption = f"📖 {recipe.name}:\n{recipe.description or ''}"
                        await update.message.reply_photo(photo=recipe.img_url, caption=caption, parse_mode="Markdown", reply_markup=get_keyboard())

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


async def random_recipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = Session()
    recipe = session.query(Recipe).order_by(func.random()).first()
    if recipe:
        if recipe.img_url:
            caption = f"📖 {recipe.name}:\n{recipe.description or ''}"
            await update.message.reply_photo(photo=recipe.img_url, caption=caption, parse_mode="Markdown", reply_markup=get_keyboard())

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
    app.run_polling()

if __name__ == "__main__":
    main()
