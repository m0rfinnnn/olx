import asyncio
import os
import json
import sqlite3
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
import uvicorn

# --- НАЛАШТУВАННЯ ---
BOT_TOKEN = "ТВІЙ_ТОКЕН"
WEB_APP_URL = "https://твій-проект.onrender.com" 

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()

# --- РОБОТА З БАЗОЮ ДАНИХ (SQLite) ---
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # Таблиця товарів
    cursor.execute('''CREATE TABLE IF NOT EXISTS products 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, price TEXT, desc TEXT, user_id TEXT)''')
    # Таблиця профілів
    cursor.execute('''CREATE TABLE IF NOT EXISTS profiles 
                      (user_id TEXT PRIMARY KEY, name TEXT, avatar TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.get("/")
async def get_index():
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

# Ендпоінт для отримання всіх товарів з бази
@app.get("/api/products")
async def get_products():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT title, price, desc FROM products ORDER BY id DESC")
    products = [{"title": row[0], "price": row[1], "desc": row[2]} for row in cursor.fetchall()]
    conn.close()
    return products

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            data = await ws.receive_json()
            if data['type'] == 'new_product':
                conn = sqlite3.connect('database.db')
                cursor = conn.cursor()
                cursor.execute("INSERT INTO products (title, price, desc) VALUES (?, ?, ?)", 
                               (data['title'], data['price'], data['desc']))
                conn.commit()
                conn.close()
                # Можна розіслати всім оновлення, але поки просто збережемо
    except Exception:
        pass

@dp.message(Command("start"))
async def start(m: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Відкрити OLX-Clone 🛒", web_app=WebAppInfo(url=WEB_APP_URL))
    ]])
    await m.answer("Вітаємо у маркетплейсі!", reply_markup=kb)

@app.on_event("startup")
async def on_startup():
    asyncio.create_task(dp.start_polling(bot))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
