#!/bin/bash
# Iniciar el bot de Telegram en segundo plano
python telegram_bot.py &

# Iniciar la aplicación Streamlit
streamlit run app.py --server.port $PORT --server.address 0.0.0.0
