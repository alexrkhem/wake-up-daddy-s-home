#!/usr/bin/env bash
echo ""
echo " ========================================"
echo "   Jarvis Personal Dashboard"
echo " ========================================"
echo ""
cd "$(dirname "$0")"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo " Created .env — please add your ANTHROPIC_API_KEY"
    echo ""
fi
echo " Starting dashboard on http://localhost:8501"
echo " Press Ctrl+C to stop."
echo ""
streamlit run app.py --server.port 8501 --server.address localhost
