#!/bin/bash
# UzSpell xizmatini ishga tushirish skripti

PROJECT_ROOT=$(pwd)
UZSPELL_DIR="$PROJECT_ROOT/uzspell"
LOG_DIR="$PROJECT_ROOT/logs"

mkdir -p "$LOG_DIR"

echo "UzSpell xizmatini to'xtatish..."
pkill -f "uzspell/app.py"

echo "UzSpell xizmatini ishga tushirish (Port 4000)..."
cd "$UZSPELL_DIR"

# Venv tekshirish
if [ ! -d "venv" ]; then
    echo "Virtual muhit yaratilmoqda..."
    python3 -m venv venv
    source venv/bin/activate
    pip install flask hunspell waitress
else
    source venv/bin/activate
fi

# Background da ishga tushirish
python3 app.py > "$LOG_DIR/uzspell.log" 2>&1 &
PID=$!

echo "✅ UzSpell xizmati ishga tushdi! PID: $PID"
echo "Loglar: tail -f logs/uzspell.log"
