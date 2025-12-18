# Legal Bridge AI
## OCR Configuration (Cyrillic-friendly)

Environment variables (optional):

- `OCR_PAGES_MAX`: Max number of PDF pages to OCR. `0` = no limit. Example: `3`.
- `OCR_DPI`: Rasterization DPI used for `pdf2image`. Default `300`.
- `USE_PADDLE`: `1` to enable PaddleOCR fallback (if installed) for tricky Cyrillic scans.
- `OCR_CHUNK_SIZE`: Process PDFs in page chunks to reduce memory/time on long files (requires PyMuPDF). Example: `5` (process 5 pages per chunk). Default: `0` (disabled).

Runtime requirements:

- Tesseract 5.x with languages: `uzb` (Uzbek Cyrillic), `uzb_latn` (Uzbek Latin), `rus` (Russian)
- PyMuPDF (optional fallback) for PDF rendering when Poppler is missing; also used for chunked processing

## Quick Benchmark

Run a quick OCR + parser benchmark against a PDF:

```bash
cd /home/rasulbek/muslim-projects/Legal-bridge-AI
export OCR_PAGES_MAX=3
export OCR_DPI=300
/home/rasulbek/muslim-projects/Legal-bridge-AI/backend/venv/bin/python scripts/benchmark.py /path/to/your.pdf
```

Output includes: `scanned`, `ocr_confidence`, `chars`, `words`, `language`, `sections_count`, and timings.

## Structured LLM Analysis

RAG/LLM now supports structured JSON output for key sections (subject/liability/price). See `section_analyses_structured` in pipeline results.

# Legal Bridge AI 🏛️⚖️

O'zbekiston Respublikasi qonunchiligiga asoslangan shartnomalarni avtomatik tahlil qilish tizimi.

![Legal Bridge AI](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.11+-green.svg)
![Django](https://img.shields.io/badge/Django-5.0-brightgreen.svg)
![React](https://img.shields.io/badge/React-18.2-61DAFB.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 📋 Loyiha haqida

Legal Bridge AI - yuridik bo'limlar uchun sun'iy intellekt asosida shartnomalarni tahlil qilish platformasi. Tizim quyidagi vazifalarni bajaradi:

- ✅ Shartnomalarni O'zR qonunchiligiga muvofiqligini tekshirish
- ✅ Xavfli va bir tomonlama bandlarni aniqlash
- ✅ Yetishmayotgan majburiy bandlarni ko'rsatish
- ✅ Risk scoring (0-100 ball)
- ✅ O'zbek (lotin/kirill) va rus tillarini qo'llab-quvvatlash
- ✅ PDF, Word, skanerlangan hujjatlar bilan ishlash
- ✅ AI asosida shartnoma tahlili (Ollama LLM)

## 🖥️ Demo Screenshots

### Bosh sahifa (Dashboard)
- Shartnomalar statistikasi
- Risk darajalari bo'yicha taqsimot
- So'nggi shartnomalar ro'yxati

### Shartnoma tahlili
- Qonunga muvofiqlik tekshiruvi
- Muammoli bandlar ro'yxati
- Risk ball va tavsiyalar

## 🏗️ Arxitektura

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│     Backend     │────▶│   AI Engine     │
│     (React)     │     │    (Django)     │     │   (LLM + RAG)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                      │                        │
         │                      ▼                        ▼
         │               ┌─────────────────┐     ┌─────────────────┐
         │               │   PostgreSQL    │     │  Vector Store   │
         │               │   (Ma'lumotlar) │     │   (ChromaDB)    │
         │               └─────────────────┘     └─────────────────┘
         │                      │
         │                      ▼
         │               ┌─────────────────┐
         └──────────────▶│   Redis/Celery  │
                         │  (Async Tasks)  │
                         └─────────────────┘
```

## 📁 Loyiha strukturasi

```
Legal-bridge-AI/
├── backend/                    # Django backend
│   ├── config/                 # Django sozlamalari
│   │   ├── settings.py         # Asosiy sozlamalar
│   │   ├── urls.py             # URL routing
│   │   └── celery.py           # Celery konfiguratsiya
│   ├── apps/
│   │   ├── contracts/          # Shartnomalar moduli
│   │   ├── analysis/           # Tahlil moduli
│   │   ├── users/              # Foydalanuvchilar
│   │   ├── reports/            # Hisobotlar
│   │   └── legal_database/     # Qonunlar bazasi
│   └── requirements.txt
│
├── ai_engine/                  # AI modullari
│   ├── ocr/                    # OCR moduli (Tesseract)
│   ├── parser/                 # Contract Parser
│   ├── compliance/             # Legal Compliance Engine
│   ├── risk_scoring/           # Risk Scoring
│   ├── rag/                    # RAG tizimi
│   ├── spelling/               # Imlo tekshiruvi
│   └── pipeline.py             # AI Pipeline
│
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/         # React komponentlar
│   │   ├── pages/              # Sahifalar
│   │   │   ├── DashboardPage   # Bosh sahifa
│   │   │   ├── ContractsPage   # Shartnomalar
│   │   │   ├── ContractDetailPage # Shartnoma tafsilotlari
│   │   │   ├── AnalysisPage    # Tahlil
│   │   │   ├── ReportsPage     # Hisobotlar
│   │   │   ├── LegalDatabasePage # Qonunlar bazasi
│   │   │   └── ProfilePage     # Profil
│   │   ├── store/              # Zustand state
│   │   └── services/           # API services
│   └── package.json
│
├── docker/                     # Docker fayllar
├── docker-compose.yml          # Docker Compose
├── Makefile                    # Make buyruqlar
└── .env.example                # Environment namuna
```

## 🛠️ Texnologiyalar

### Backend
| Texnologiya | Versiya | Vazifa |
|-------------|---------|--------|
| Django | 5.0 | Web framework |
| Django REST Framework | 3.14+ | REST API |
| Celery | 5.3+ | Asinxron vazifalar |
| PostgreSQL | 15+ | Ma'lumotlar bazasi |
| Redis | 7+ | Cache va queue |
| SimpleJWT | 5.3+ | JWT Authentication |

### AI/ML
| Texnologiya | Vazifa |
|-------------|--------|
| Ollama | Local LLM (Llama 3.1) |
| LangChain | LLM orchestration |
| ChromaDB | Vector database |
| Tesseract OCR | Rasm → Matn |
| Sentence Transformers | Embeddings |

### Frontend
| Texnologiya | Versiya | Vazifa |
|-------------|---------|--------|
| React | 18.2 | UI framework |
| Vite | 5.0 | Build tool |
| TailwindCSS | 3.4 | Styling |
| React Query | 5.17 | Data fetching |
| Zustand | 4.4 | State management |
| React Router | 6.21 | Routing |
| Recharts | 2.10 | Grafiklar |

## 🚀 Ishga tushirish

### Talablar
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Ollama (AI uchun)

### 1. Loyihani klonlash

```bash
git clone https://github.com/muslimbek77/Legal-bridge-AI.git
cd Legal-bridge-AI
```

### 2. Backend sozlash

```bash
# Virtual muhit yaratish
python -m venv venv
source venv/bin/activate  # Linux/Mac
# yoki
.\venv\Scripts\activate  # Windows

# Dependencies o'rnatish
cd backend
pip install -r requirements.txt

# .env faylini sozlash
cp ../.env.example ../.env
# .env faylini tahrirlang

# Database migratsiyalar
python manage.py migrate
python manage.py createsuperuser
```

### 3. Frontend sozlash

```bash
cd frontend
npm install
```

### 4. AI modellarni sozlash

```bash
# Ollama o'rnatish (Linux)
curl -fsSL https://ollama.com/install.sh | sh

# Model yuklash
ollama pull llama3.1

# Tesseract o'rnatish (Ubuntu/Debian)
sudo apt install tesseract-ocr tesseract-ocr-uzb tesseract-ocr-rus
```

### 5. Loyihani ishga tushirish

#### Backend
```bash
# Terminal 1: Django server
cd backend
source ../venv/bin/activate
python manage.py runserver 0.0.0.0:8000

# Terminal 2: Celery worker
cd backend
source ../venv/bin/activate
celery -A config worker -l INFO
```

#### Frontend
```bash
# Terminal 3: React development server
cd frontend
npm run dev
```

### 6. Brauzerni ochish

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/v1/
- Admin panel: http://localhost:8000/admin/

### Docker bilan ishga tushirish

```bash
# Barcha servislarni ishga tushirish
docker-compose up -d

# Loglarni ko'rish
docker-compose logs -f
```

## 📊 AI Modullar

### 1. Contract Parser (`ai_engine/parser/`)
Shartnoma bo'limlarini avtomatik aniqlaydi:
- Tomonlar haqida ma'lumot
- Shartnoma predmeti
- Huquq va majburiyatlar
- Muddat va shartlar
- Javobgarlik bandlari
- To'lov shartlari
- Nizolarni hal qilish

### 2. Legal Compliance Engine (`ai_engine/compliance/`)
O'zbekiston qonunlariga moslikni tekshiradi:
- O'zR Fuqarolik kodeksi
- Mehnat kodeksi
- Soliq kodeksi
- Davlat xaridlari to'g'risidagi qonun
- Iste'molchilar huquqlarini himoya qilish

### 3. Risk Scoring (`ai_engine/risk_scoring/`)
Xavf darajasini baholaydi:

| Ball | Daraja | Tavsif |
|------|--------|--------|
| 0-30 | 🔴 Yuqori xavf | Jiddiy muammolar mavjud |
| 31-70 | 🟡 O'rtacha xavf | E'tibor talab qiladigan joylar bor |
| 71-100 | 🟢 Minimal xavf | Qonunlarga mos |

### 4. OCR Module (`ai_engine/ocr/`)
Skanerlangan hujjatlardan matn ajratish:
- PDF rasmlardan matn olish
- O'zbek va rus tillarini qo'llab-quvvatlash
- Avtomatik til aniqlash

## 📝 API Endpointlar

### Authentication
| Method | Endpoint | Tavsif |
|--------|----------|--------|
| POST | `/api/v1/auth/register/` | Ro'yxatdan o'tish |
| POST | `/api/v1/auth/login/` | Kirish |
| POST | `/api/v1/auth/logout/` | Chiqish |
| POST | `/api/v1/auth/token/refresh/` | Token yangilash |

### Contracts
| Method | Endpoint | Tavsif |
|--------|----------|--------|
| GET | `/api/v1/contracts/` | Shartnomalar ro'yxati |
| POST | `/api/v1/contracts/` | Yangi shartnoma yaratish |
| GET | `/api/v1/contracts/{id}/` | Shartnoma tafsilotlari |
| DELETE | `/api/v1/contracts/{id}/` | Shartnomani o'chirish |
| POST | `/api/v1/contracts/{id}/analyze/` | Tahlil boshlash |

### Analysis
| Method | Endpoint | Tavsif |
|--------|----------|--------|
| GET | `/api/v1/analysis/` | Tahlillar ro'yxati |
| GET | `/api/v1/analysis/{id}/` | Tahlil natijasi |
| GET | `/api/v1/analysis/stats/` | Statistika |

### Reports
| Method | Endpoint | Tavsif |
|--------|----------|--------|
| GET | `/api/v1/reports/` | Hisobotlar |
| GET | `/api/v1/reports/export/pdf/{id}/` | PDF export |

### Legal Database
| Method | Endpoint | Tavsif |
|--------|----------|--------|
| GET | `/api/v1/legal/laws/` | Qonunlar ro'yxati |
| GET | `/api/v1/legal/articles/` | Moddalar |
| GET | `/api/v1/legal/search/` | Qidiruv |

## ⚙️ Muhit o'zgaruvchilari (.env)

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=legal_bridge_db
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1

# Frontend
VITE_API_URL=http://localhost:8000
```

## 🧪 Testlar

```bash
# Backend testlar
cd backend
python manage.py test

# Frontend testlar
cd frontend
npm test
```

## 📈 Loyiha statistikasi

- **Backend**: Django 5.0 + DRF
- **Frontend**: React 18 + TailwindCSS
- **AI**: Ollama (Llama 3.1)
- **Database**: PostgreSQL + Redis
- **Sahifalar**: 12 ta (Dashboard, Contracts, Analysis, Reports, va boshqalar)

## 🤝 Hissa qo'shish

1. Fork qiling
2. Feature branch yarating (`git checkout -b feature/amazing-feature`)
3. O'zgarishlarni commit qiling (`git commit -m 'Add amazing feature'`)
4. Push qiling (`git push origin feature/amazing-feature`)
5. Pull Request oching

## 📄 Litsenziya

MIT License - batafsil [LICENSE](LICENSE) faylida.

## 👥 Muallif

**Muslimbek** - [GitHub](https://github.com/muslimbek77)

## 📞 Aloqa

Savollar va takliflar uchun:
- GitHub Issues: [Issues](https://github.com/muslimbek77/Legal-bridge-AI/issues)
- Email: legal-bridge-ai@example.com

---

⭐ Agar loyiha foydali bo'lsa, GitHub'da yulduzcha qo'yishni unutmang!
