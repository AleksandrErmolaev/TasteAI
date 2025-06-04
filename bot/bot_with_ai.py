import re
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, func
from models import Recipe
from Model.Model import recommend_recipes, format_recommendations
from telegram.helpers import escape_markdown

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

                    ingredients_list = [ing.strip() for ing in re.split(r'[;,]', recipe.ingredients) if ing.strip()]
                    ingredients_text = "\n".join(ingredients_list)

                    ingredients_and_instructions = f"\n{ingredients_text}\n\nИнструкция:\n{recipe.instructions}"
                    escaped_text = escape_markdown(ingredients_and_instructions, version=2)
                    await update.message.reply_text(
                        escaped_text,
                        parse_mode="MarkdownV2",
                        reply_markup=get_keyboard()
                    )
            else:
                await update.message.reply_text("Ничего не найдено.", reply_markup=get_keyboard())
        elif action == "recommend":
            user_ingredients = [ing.strip() for ing in user_input.split(',')]
            recommendations = recommend_recipes(user_ingredients)
            from telegram import InlineKeyboardMarkup, InlineKeyboardButton

            if recommendations:
                buttons = [
                    [InlineKeyboardButton(f"{rec['name']} ({rec['match_count']} совп.)", callback_data=f"recipe_{rec['id']}")]
                    for rec in recommendations
                ]
                reply_markup = InlineKeyboardMarkup(buttons)
                await update.message.reply_text("Рекомендуемые рецепты:", reply_markup=reply_markup)
                context.user_data["awaiting"] = None
            else:
                await update.message.reply_text("Не найдено подходящих рецептов. Попробуйте другие ингредиенты.", reply_markup=get_keyboard())
                context.user_data["awaiting"] = None

        elif action == "instructions":
            try:
                recipe_id = int(user_input)
                recipe = session.query(Recipe).get(recipe_id)
                if recipe:
                    if recipe.img_url:
                        caption = f"📖 {recipe.name}:\n{recipe.description or ''}"
                        await update.message.reply_photo(photo=recipe.img_url, caption=caption, parse_mode="Markdown", reply_markup=get_keyboard())

                    ingredients_list = [ing.strip() for ing in re.split(r'[;,]', recipe.ingredients) if ing.strip()]
                    ingredients_text = "\n".join(ingredients_list)

                    ingredients_and_instructions = f"Ингредиенты:\n{ingredients_text}\n\nИнструкции:\n{recipe.instructions}"
                    escaped_text = escape_markdown(ingredients_and_instructions, version=2)
                    await update.message.reply_text(
                        escaped_text,
                        parse_mode="MarkdownV2",
                        reply_markup=get_keyboard()
                    )
                else:
                    await update.message.reply_text("Рецепт не найден.", reply_markup=get_keyboard())
            except ValueError:
                await update.message.reply_text("Введите корректный ID.", reply_markup=get_keyboard())
        else:
            await update.message.reply_text("Выберите действие через /start.", reply_markup=get_keyboard())

    session.close()


async def random_recipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = Session()
    recipe = session.query(Recipe).order_by(func.random()).first()
    if recipe:
        if recipe.img_url:
            caption = f"📖 {recipe.name}:\n{recipe.description or ''}"
            await update.message.reply_photo(photo=recipe.img_url, caption=caption, parse_mode="Markdown", reply_markup=get_keyboard())

        ingredients_list = [ing.strip() for ing in re.split(r'[;,]', recipe.ingredients) if ing.strip()]
        ingredients_text = "\n".join(ingredients_list)

        ingredients_and_instructions = f"\n{ingredients_text}\n\nИнструкция:\n{recipe.instructions}"
        escaped_text = escape_markdown(ingredients_and_instructions, version=2)
        await update.message.reply_text(
            escaped_text,
            parse_mode="MarkdownV2",
            reply_markup=get_keyboard()
        )
    else:
        await update.message.reply_text("Нет рецептов.", reply_markup=get_keyboard())
    session.close()


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    session = Session()

    if query.data.startswith("recipe_"):
        recipe_id = int(query.data.split("_")[1])
        recipe = session.get(Recipe, recipe_id)
        if recipe:
            if recipe.img_url:
                caption = f"📖 {recipe.name}:\n{recipe.description or ''}"
                await query.message.reply_photo(photo=recipe.img_url, caption=caption, parse_mode="Markdown", reply_markup=get_keyboard())

            ingredients_list = [ing.strip() for ing in re.split(r'[;,]', recipe.ingredients) if ing.strip()]
            ingredients_text = "\n".join(ingredients_list)

            ingredients_and_instructions = f"Ингредиенты:\n{ingredients_text}\n\nИнструкции:\n{recipe.instructions}"
            escaped_text = escape_markdown(ingredients_and_instructions, version=2)
            await query.message.reply_text(
                escaped_text,
                parse_mode="MarkdownV2",
                reply_markup=get_keyboard()
            )
        else:
            await query.message.reply_text("Рецепт не найден.", reply_markup=get_keyboard())

    session.close()


from telegram.ext import CallbackQueryHandler

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("Бот запущен.")
    app.run_polling()

    print("Бот запущен.")
    app.run_polling()


if __name__ == "__main__":
    main()
