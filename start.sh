#!/bin/bash
# start.sh — скрипт запуска бота

echo "🚀 Запуск бота Historian..."
# Проверяем наличие файла quotes_data.json, если нет — создаём пустой
if [ ! -f quotes_data.json ]; then
    echo "{}" > quotes_data.json
    echo "📄 quotes_data.json создан"
fi

# Запуск бота
python3 bot.py
