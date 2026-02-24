import asyncio
import json
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
import uvicorn

# --- НАЛАШТУВАННЯ ---
BOT_TOKEN = "8483109575:AAHN0-ZVB37URDe4IXCNaRuKfFLBnUlSq-4"
# Коли запустиш сервер (наприклад, на Render або Railway), сюди вставиш його адресу:
WEB_APP_URL = "https://olx-1-bou2.onrender.com" 

# --- ТЕЛЕГРАМ БОТ ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Спільна малювалка 🎨", 
            web_app=WebAppInfo(url=WEB_APP_URL)
        )]
    ])
    await message.answer("Заходь і малюй разом з іншими!", reply_markup=markup)

# --- WEB СЕРВЕР ТА WEBSOCKETS ---
app = FastAPI()

# Зберігаємо всі активні підключення
active_connections = []

@app.get("/")
async def get_html():
    # Віддаємо наш HTML файл (його створимо в наступному кроці)
    with open("index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            # Отримуємо координати від одного користувача...
            data = await websocket.receive_text()
            # ...і розсилаємо всім іншим
            for connection in active_connections:
                if connection != websocket:
                    await connection.send_text(data)
    except WebSocketDisconnect:
        active_connections.remove(websocket)

# --- ЗАПУСК УСЬОГО РАЗОМ ---
async def start_bot():
    await dp.start_polling(bot)

@app.on_event("startup")
async def on_startup():
    asyncio.create_task(start_bot())

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Запускаємо сервер на порту 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
