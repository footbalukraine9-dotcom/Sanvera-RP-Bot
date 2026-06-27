import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# =====================================================================
# НАЛАШТУВАННЯ: ТОКЕН ТА ID ТВОЄЇ ГРУПИ
# =====================================================================
BOT_TOKEN = "8726373688:AAHU6lYQ0xJQmljsIulm72iFdC_BxJFIR4U"
GROUP_CHAT_ID = -1004352368487  # Твій ID групи Sanvera RP Support
# =====================================================================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Словники для збереження стану
active_tickets = {}  # {user_id: {"operator_id": id, "operator_name": str, "main_msg_id": id}}
msg_to_user = {}     # {message_id_in_group: user_id}

# Професійне привітання для гравця
@dp.message(Command("start"), F.chat.type == "private")
async def cmd_start(message: types.Message):
    welcome_text = (
        "✨ <b>SANVERA RP • СЛУЖБА ПІДТРИМКИ</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Вітаємо! Ви звернулися до офіційного центру допомоги.\n\n"
        "📝 <b>Будь ласка, опишіть вашу проблему в одному повідомленні:</b>\n"
        "• Вкажіть ваш нікнейм у грі\n"
        "• Суть проблеми або суть вашої скарги\n"
        "• Додайте скріншоти (якщо є)\n\n"
        "⏳ <i>Наші вільні оператори вже готові розглянути ваше звернення. Просто напишіть текст нижче.</i>"
    )
    await message.answer(welcome_text, parse_mode="HTML")

# Гравець пише в ПП боту
@dp.message(F.chat.type == "private")
async def handle_player_message(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.full_name

    if user_id in active_tickets:
        reply_msg = await bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=f"<b>👤 Гравець {user_name} додає:</b>\n{message.text}",
            parse_mode="HTML"
        )
        msg_to_user[reply_msg.message_id] = user_id
        await message.answer("✅ Додаткову інформацію відправлено оператору.")
        return

    builder = InlineKeyboardBuilder().button(text="🎯 Прийняти тікет", callback_data=f"take_{user_id}")
    
    main_msg = await bot.send_message(
        chat_id=GROUP_CHAT_ID,
        text=(
            f"<b>🚨 НАДІЙШЛО НОВЕ ЗВЕРНЕННЯ</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Гравець:</b> {message.from_user.mention_html()}\n"
            f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
            f"📝 <b>Текст:</b> {message.text}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 <i>Натисніть кнопку нижче, щоб стати оператором.</i>"
        ),
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    
    active_tickets[user_id] = {
        "operator_id": None,
        "operator_name": None,
        "main_msg_id": main_msg.message_id
    }
    msg_to_user[main_msg.message_id] = user_id
    await message.answer("✅ Ваше звернення доставлено операторам. Очікуйте на відповідь.")

# Кнопка "Прийняти тікет"
@dp.callback_query(F.data.startswith("take_"))
async def handle_take_ticket(call: types.CallbackQuery):
    user_id = int(call.data.split("_")[1])
    operator_id = call.from_user.id
    operator_name = call.from_user.full_name
    
    if user_id in active_tickets:
        if active_tickets[user_id]["operator_id"] is not None:
            await call.answer("❌ Цей тікет вже взяв інший оператор!", show_alert=True)
            return
            
        active_tickets[user_id]["operator_id"] = operator_id
        active_tickets[user_id]["operator_name"] = operator_name
        
        builder = InlineKeyboardBuilder().button(text="🔒 Закрити тікет", callback_data=f"close_{user_id}")
        
        await call.message.edit_text(
            f"<b>✅ ТІКЕТ В РОБОТІ</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Гравець ID:</b> <code>{user_id}</code>\n"
            f"👨‍💻 <b>Оператор:</b> {operator_name}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚙️ <i>ВІДПОВІДАЙТЕ гравцю через функцію REPLY (Відповісти) на це повідомлення.</i>",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        await call.answer("Ви успішно взяли тікет!")
        
        await bot.send_message(
            chat_id=user_id,
            text=f"👨‍💻 <b>Оператор {operator_name} приєднався до діалогу!</b>\nЗадайте ваше питання або очікуйте відповіді.",
            parse_mode="HTML"
        )

# Кнопка "Закрити тікет"
@dp.callback_query(F.data.startswith("close_"))
async def handle_close_ticket(call: types.CallbackQuery):
    user_id = int(call.data.split("_")[1])
    
    if user_id in active_tickets:
        if active_tickets[user_id]["operator_id"] != call.from_user.id:
            await call.answer("❌ Ви не можете закрити чужий тікет!", show_alert=True)
            return
            
        try:
            await bot.send_message(
                chat_id=user_id,
                text="🔒 <b>Ваш тікет був успешно закритий оператором.</b>\nДякуємо за звернення! Якщо виникнуть нові питання — пишіть знову /start.",
                parse_mode="HTML"
            )
        except Exception:
            pass
            
        await call.message.edit_text(
            f"🔒 <b>ТІКЕТ ЗАКРИТО</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Гравець ID:</b> <code>{user_id}</code>\n"
            f"👨‍💻 <b>Працював оператор:</b> {active_tickets[user_id]['operator_name']}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ Проблему успішно вирішено.",
            parse_mode="HTML"
        )
        await call.answer("Тікет закрито!")
        
        del active_tickets[user_id]

# Відповідь оператора через Reply
@dp.message(F.chat.type.in_({"group", "supergroup"}), F.reply_to_message)
async def handle_operator_reply(message: types.Message):
    reply_id = message.reply_to_message.message_id
    user_id = msg_to_user.get(reply_id)

    if not user_id or user_id not in active_tickets:
        return

    if active_tickets[user_id]["operator_id"] != message.from_user.id:
        await message.reply("⚠️ Ви не можете сюди відповідати. Цей тікет закріплено за іншим оператором!")
        return

    try:
        await bot.send_message(
            chat_id=user_id,
            text=f"<b>✉️ Відповідь від оператора:</b>\n{message.text}",
            parse_mode="HTML"
        )
        await message.reply("✅ Відповідь надіслана гравцю.")
    except Exception:
        await message.reply("❌ Не вдалося доставити. Гравець заблокував бота.")

async def main():
    print("-----------------------------------------")
    print("   SANVERA REPLIER-BOT IS RUNNING NOW!   ")
    print("-----------------------------------------")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())