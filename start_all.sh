#!/bin/bash

# Ranglar
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Legal Bridge AI loyihasini ishga tushirish...${NC}"

# Loyiha papkasini aniqlash
PROJECT_ROOT=$(pwd)
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# Virtual muhitni tekshirish
if [ -d "$BACKEND_DIR/venv" ]; then
    source "$BACKEND_DIR/venv/bin/activate"
else
    echo -e "${RED}Virtual muhit topilmadi! (backend/venv)${NC}"
    exit 1
fi

# Eski jarayonlarni tozalash
echo -e "${BLUE}Eski jarayonlarni tozalash...${NC}"
pkill -f "runserver"
pkill -f "celery"
pkill -f "vite"

# Loglar uchun papka
mkdir -p "$PROJECT_ROOT/logs"

# 1. Django Serverni ishga tushirish (Port 3000)
echo -e "${GREEN}Django serverni ishga tushirish (Port 3000)...${NC}"
cd "$BACKEND_DIR"
python manage.py runserver 0.0.0.0:3000 > "$PROJECT_ROOT/logs/django.log" 2>&1 &
DJANGO_PID=$!

# 2. Celery Workerni ishga tushirish
echo -e "${GREEN}Celery Workerni ishga tushirish...${NC}"
celery -A config worker -l INFO --pool=solo --concurrency=2 --logfile="$PROJECT_ROOT/logs/celery_worker.log" &
WORKER_PID=$!

# 3. Celery Beatni ishga tushirish
echo -e "${GREEN}Celery Beatni ishga tushirish...${NC}"
celery -A config beat -l INFO --logfile="$PROJECT_ROOT/logs/celery_beat.log" &
BEAT_PID=$!

# 3.5. UzSpell xizmatini ishga tushirish
echo -e "${GREEN}UzSpell xizmatini ishga tushirish (Port 4000)...${NC}"
cd "$PROJECT_ROOT/uzspell"
# Agar venv bo'lmasa yaratish
if [ ! -d "venv" ]; then
    python3 -m venv venv
    source venv/bin/activate
    pip install flask hunspell waitress
else
    source venv/bin/activate
fi
python3 app.py > "$PROJECT_ROOT/logs/uzspell.log" 2>&1 &
UZSPELL_PID=$!

# 4. Frontendni ishga tushirish
echo -e "${GREEN}Frontendni ishga tushirish (Port 3001)...${NC}"
cd "$FRONTEND_DIR"
npm run dev > "$PROJECT_ROOT/logs/frontend.log" 2>&1 &
FRONTEND_PID=$!

echo -e "${BLUE}Barcha xizmatlar ishga tushdi!${NC}"
echo -e "Django Log: ${BLUE}tail -f logs/django.log${NC}"
echo -e "Celery Worker Log: ${BLUE}tail -f logs/celery_worker.log${NC}"
echo -e "Frontend Log: ${BLUE}tail -f logs/frontend.log${NC}"
echo -e "${RED}To'xtatish uchun Ctrl+C bosing${NC}"

# To'xtatish funksiyasi
cleanup() {
    echo -e "\n${RED}Barcha xizmatlar to'xtatilmoqda...${NC}"
    kill $DJANGO_PID $WORKER_PID $BEAT_PID $FRONTEND_PID $UZSPELL_PID
    exit
}

trap cleanup SIGINT SIGTERM

wait
