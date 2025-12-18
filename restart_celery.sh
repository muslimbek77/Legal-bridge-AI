#!/bin/bash
# Celery worker'ni qayta ishga tushirish skripti

echo "Celery worker va beatni to'xtatish..."

# Eski celery processlarni to'xtatish
pkill -f "celery worker"
pkill -f "celery beat"

# Bir oz kutish
sleep 2

echo "Celery worker'ni ishga tushirish..."

# Backend papkaga o'tish
cd /home/rasulbek/muslim-projects/Legal-bridge-AI/backend

# Virtual environmentni aktivlashtirish va celery ishga tushirish
source venv/bin/activate

# Celery worker'ni background'da ishga tushirish
celery -A config worker -l INFO --logfile=/tmp/celery_worker.log 2>&1 &

# Worker PIDni saqlash
WORKER_PID=$!
echo "Celery worker started with PID: $WORKER_PID"
echo $WORKER_PID > /tmp/celery_worker.pid

# (Ixtiyoriy) Celery beat'ni ham ishga tushirish
# celery -A config beat -l INFO --logfile=/tmp/celery_beat.log 2>&1 &
# BEAT_PID=$!
# echo "Celery beat started with PID: $BEAT_PID"
# echo $BEAT_PID > /tmp/celery_beat.pid

echo "✅ Celery worker ishga tushdi!"
echo "Loglarni ko'rish: tail -f /tmp/celery_worker.log"
echo "Worker to'xtatish: kill \$(cat /tmp/celery_worker.pid)"
