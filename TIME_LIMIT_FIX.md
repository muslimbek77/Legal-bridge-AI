# ⏱️ Celery Time Limit Configuration - Fix for TimeLimitExceeded

## Problem
Production server'da Celery tasklar 360 soniya (6 daqiqa) o'tida vaqt limitiga duch kelyapti:
```
Hard time limit (360s) exceeded for apps.analysis.tasks.analyze_contract_task
billiard.exceptions.TimeLimitExceeded: TimeLimitExceeded(360,)
```

Tahlil jarayoni aslida 300-400 soniya olmoqda, shuning uchun bu qisqa limit muammo tug'dirmoqda.

## Solution

### 1. Backend Settings (`config/settings.py`)
Umumiy Celery time limitlarini 20 va 25 minutaga ko'tarish:
- `CELERY_TASK_SOFT_TIME_LIMIT = 1200` (20 min - graceful shutdown)
- `CELERY_TASK_TIME_LIMIT = 1500` (25 min - hard kill)

### 2. Task Definition (`apps/analysis/tasks.py`)
`analyze_contract_task`'da:
- Old: `soft_time_limit=300, time_limit=360`
- New: `soft_time_limit=1200, time_limit=1500`

### 3. Docker Compose (`docker-compose.yml`)
Celery worker container startida:
```bash
command: celery -A config worker -l info --concurrency=2 --hostname=worker@%h \
  --soft-time-limit=1200 --time-limit=1500
```

### 4. Local Dev Script (`restart_celery.sh`)
Worker ishga tushirish:
```bash
celery -A config worker -l INFO \
  --pool=solo --concurrency=2 \
  --soft-time-limit=1200 --time-limit=1500 \
  --logfile=/tmp/celery_worker.log
```

### 5. Production Service (`legalbridge-celery.service`)
Systemd unit file template shaklida tayyorlandi. Production server'da:
```bash
sudo cp legalbridge-celery.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl restart legalbridge-celery
```

## Timeline

**Soft Time Limit (1200s = 20 min)**
- Task'dan `SoftTimeLimitExceeded` exception o't-keradi
- Code buni catch qilishi va graceful shutdown qilishi mumkin
- Task'ga nisbatan oshish-olib selimasliligi

**Hard Time Limit (1500s = 25 min)**
- Agar task hali shunda ishlab tursa, worker uni force kill qiladi
- Task qayta urinish (retry) mexanizmi ishga tushadi

## Testing

Production server'da Celery worker'ni qayta ishga tushirish:
```bash
# Agar systemd service bo'lsa:
sudo systemctl restart legalbridge-celery

# Agar to'g'ri Docker compose bo'lsa:
docker-compose down && docker-compose up -d celery

# Logs'ni kuzatish:
journalctl -u legalbridge-celery.service -f
# yoki
docker-compose logs -f celery
```

## Notes

- Vaqt limitlari production va dev muhitlar uchun o'xshash sozlandy
- SoftTimeLimitExceeded exception handling `apps/analysis/tasks.py`'da mavjud
- Retry logic max 3 marta qayta ishlaydi
