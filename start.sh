# start.py
import os
import subprocess

# Проверяем наличие файла quotes_data.json
if not os.path.exists("quotes_data.json"):
    with open("quotes_data.json", "w", encoding="utf-8") as f:
        f.write("{}")
    print("📄 quotes_data.json создан")

# Запуск бота
os.system("python3 bot.py")
