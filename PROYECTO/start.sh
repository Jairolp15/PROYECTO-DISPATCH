#!/bin/bash

# Iniciar el bot de Telegram en segundo plano
echo "Iniciando Telegram Bot..."
python telegram_bot.py &

# Iniciar Streamlit
echo "Iniciando Streamlit Dashboard..."
streamlit run app.py --server.port ${PORT:-8501} --server.address 0.0.0.0
