# Legal Bridge AI 🏛️⚖️

O'zbekiston Respublikasi qonunchiligiga asoslangan shartnomalarni avtomatik tahlil qilish tizimi.

## 📋 Loyiha haqida

Legal Bridge AI - yuridik bo'limlar uchun sun'iy intellekt asosida shartnomalarni tahlil qilish platformasi. Tizim quyidagi vazifalarni bajaradi:

- ✅ Shartnomalarni O'zR qonunchiligiga muvofiqligini tekshirish
- ✅ Xavfli va bir tomonlama bandlarni aniqlash
- ✅ Yetishmayotgan majburiy bandlarni ko'rsatish
- ✅ Risk scoring (0-100 ball)
- ✅ O'zbek (lotin/kirill) va rus tillarini qo'llab-quvvatlash
- ✅ PDF, Word, skanerlangan hujjatlar bilan ishlash

## 🏗️ Arxitektura

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│     Backend     │────▶│   AI Engine     │
│   (React/Vue)   │     │    (Django)     │     │   (LLM + RAG)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │                        │
                               ▼                        ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │   PostgreSQL    │     │  Vector Store   │
                        │   (Ma'lumotlar) │     │   (ChromaDB)    │
                        └─────────────────┘     └─────────────────┘
```

## 📁 Loyiha strukturasi

```
Legal-bridge-AI/
├── backend/                    # Django backend
│   ├── config/                 # Django sozlamalari
│   ├── apps/
│   │   ├── contracts/          # Shartnomalar moduli
│   │   ├── analysis/           # Tahlil moduli
│   │   ├── users/              # Foydalanuvchilar
│   │   └── reports/            # Hisobotlar
│   └── requirements.txt
│
├── ai_engine/                  # AI modullari
│   ├── ocr/                    # OCR moduli
│   ├── parser/                 # Contract Parser
│   ├── compliance/             # Legal Compliance Engine
│   ├── risk_scoring/           # Risk Scoring
│   ├── rag/                    # RAG tizimi
│   └── models/                 # LLM modellar
│
├── legal_database/             # Qonunlar bazasi
│   ├── civil_code/             # Fuqarolik kodeksi
│   ├── labor_code/             # Mehnat kodeksi
│   ├── tax_code/               # Soliq kodeksi
│   ├── procurement/            # Davlat xaridlari
│   └── templates/              # Shartnoma shablonlari
│
├── frontend/                   # React frontend
│
├── docker/                     # Docker fayllar
│
└── docs/                       # Hujjatlar
```

## 🛠️ Texnologiyalar

### Backend
- **Django 5.0** - Web framework
- **Django REST Framework** - API
- **Celery** - Asinxron vazifalar
- **PostgreSQL** - Ma'lumotlar bazasi
- **Redis** - Cache va queue

### AI/ML
- **LangChain** - LLM orchestration
- **ChromaDB** - Vector database
- **Tesseract/PaddleOCR** - OCR
- **Sentence Transformers** - Embeddings
- **Ollama** - Local LLM (Llama 3.1, Qwen2.5)

### Frontend
- **React 18** - UI framework
- **TailwindCSS** - Styling
- **React Query** - Data fetching

## 🚀 Ishga tushirish

### 1. Muhit sozlash

```bash
# Virtual muhit yaratish
python -m venv venv
source venv/bin/activate  # Linux/Mac
# yoki
.\venv\Scripts\activate  # Windows

# Backend dependencies
cd backend
pip install -r requirements.txt

# Frontend dependencies
cd ../frontend
npm install
```

### 2. Database sozlash

```bash
# PostgreSQL database yaratish
createdb legal_bridge_db

# Migratsiyalar
cd backend
python manage.py migrate
python manage.py createsuperuser
```

### 3. AI modellarni yuklash

```bash
# Ollama o'rnatish va model yuklash
ollama pull llama3.1
ollama pull qwen2.5:14b

# Tesseract o'rnatish
sudo apt install tesseract-ocr tesseract-ocr-uzb tesseract-ocr-rus
```

### 4. Loyihani ishga tushirish

```bash
# Backend
cd backend
python manage.py runserver

# Celery worker
celery -A config worker -l info

# Frontend
cd frontend
npm run dev
```

### Docker bilan ishga tushirish

```bash
docker-compose up -d
```

## 📊 AI Modullar

### 1. Contract Parser
Shartnoma bo'limlarini avtomatik aniqlaydi:
- Tomonlar haqida ma'lumot
- Huquq va majburiyatlar
- Muddat va shartlar
- Javobgarlik
- To'lovlar
- Nizolarni hal qilish

### 2. Legal Compliance Engine
Qonunlarga moslikni tekshiradi:
- O'zR Fuqarolik kodeksi
- Mehnat kodeksi
- Soliq kodeksi
- Davlat xaridlari to'g'risidagi qonun

### 3. Risk Scoring
Xavf darajasini baholaydi:
- **0-30 ball**: Yuqori xavf ⚠️
- **30-70 ball**: O'rtacha xavf ⚡
- **70-100 ball**: Minimal xavf ✅

## 📝 API Endpointlar

| Method | Endpoint | Tavsif |
|--------|----------|--------|
| POST | `/api/contracts/upload/` | Shartnoma yuklash |
| GET | `/api/contracts/{id}/` | Shartnoma ma'lumotlari |
| POST | `/api/analysis/analyze/` | Tahlil boshlash |
| GET | `/api/analysis/{id}/report/` | Tahlil natijasi |
| GET | `/api/reports/export/pdf/` | PDF export |

## 🤝 Hissa qo'shish

1. Fork qiling
2. Feature branch yarating (`git checkout -b feature/amazing-feature`)
3. Commit qiling (`git commit -m 'Add amazing feature'`)
4. Push qiling (`git push origin feature/amazing-feature`)
5. Pull Request oching

## 📄 Litsenziya

MIT License - batafsil [LICENSE](LICENSE) faylida.

## 📞 Aloqa

Savollar va takliflar uchun: legal-bridge-ai@example.com
