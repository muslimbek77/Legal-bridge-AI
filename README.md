# Legal Bridge AI 🏛️⚖️

**Legal Bridge AI** – O'zbekiston yuridik sohasini raqamlashtirish va shartnomalar bilan ishlash jarayonini avtomatlashtirish uchun mo'ljallangan sun'iy intellekt platformasi. Ushbu tizim shartnomalarni chuqur tahlil qiladi, risklarni aniqlaydi va qonunchilikka mosligini tekshiradi.

---

## 🚀 Asosiy Imkoniyatlar

### 1. 📄 OCR va Hujjatni Tanib Olish
*   **Ko'p tilli OCR:** O'zbek (Kirill/Lotin) va Rus tillaridagi skaner qilingan PDF va rasmlarni yuqori aniqlikda o'qish.
*   **Avtomatik To'g'rilash:** `ai_engine` orqali OCR natijasidagi umumiy xatolarni (masalan, `h` -> `ҳ`, `k` -> `q`) avtomatik tuzatish.
*   **Format:** PDF, DOCX, va Rasm formatlarini qo'llab-quvvatlaydi.

### 2. 🔍 Shartnoma Tahlili (AI & Parsing)
*   **Strukturali Tahlil:** Shartnomaning asosiy qismlarini (Tomonlar, Predmet, Narx, Huquq va Majburiyatlar) ajratib olish.
*   **Yuridik Compliance:** O'zbekiston Respublikasi qonunchiligi asosida shartnoma bandlarini tekshirish.
*   **Risk Scoring:** Shartnomaning xavflilik darajasini, muvozanatini va aniqligini baholash (0-100 ball).
*   **LLM Integratsiyasi:** **Gemini 1.5 Flash** (yoki OpenAI) yordamida shartnoma mazmunini chuqur tahlil qilish va xulosa berish.

### 3. ✍️ Imlo va Uslubiy Tekshiruv
*   **UzSpell Engine:** Matn.uz va Hunspell asosidagi maxsus imlo tekshiruvi.
*   **Yuridik Lug'at:** Shartnomalarda ko'p uchraydigan yuridik terminlar va ruscha so'zlar uchun maxsus "whitelist" va korreksiya qoidalari.

### 4. 📊 Hisobot va Monitoring
*   Tahlil natijalarini PDF formatida yuklab olish.
*   Shartnomalar reestri va status monitoringi.

---

## 🛠️ Texnologik Stack

### Backend
*   **Python 3.11+**
*   **Django 5.0 & Django REST Framework:** API va asosiy logika.
*   **Celery & Redis:** Asinxron vazifalar (OCR, AI tahlil) uchun navbatlar tizimi.
*   **Tesseract OCR 5:** Matnni tanib olish.
*   **Google Gemini Pro / OpenAI:** Generativ AI tahlil.

### Frontend
*   **React 18 (Vite):** Zamonaviy va tezkor UI.
*   **Tailwind CSS & Ant Design:** Responsive va qulay dizayn.
*   **React Query:** Server state management.

### Infra & Tools
*   **Docker & Docker Compose:** Containerization.
*   **PostgreSQL:** Relatsion ma'lumotlar bazasi.
*   **UzSpell Microservice:** Mahalliy imlo tekshirish servisi.

---

## 📥 O'rnatish va Ishga Tushirish

### 1. Talablar
*   Linux (Ubuntu 22.04+ tavsiya etiladi)
*   Python 3.11+
*   Node.js 18+
*   Tesseract OCR (`sudo apt install tesseract-ocr tesseract-ocr-uzb tesseract-ocr-uzb-cyrl`)
*   Redis (`sudo apt install redis-server`)

### 2. Loyihani o'rnatish

```bash
# Repozitoriyni klonlash
git clone https://github.com/username/legal-bridge-ai.git
cd legal-bridge-ai

# Backend muhitini sozlash
python3 -m venv backend/venv
source backend/venv/bin/activate
pip install -r backend/requirements.txt
pip install -r uzspell/requirements.txt

# Environment o'zgaruvchilarni sozlash (.env faylini yarating)
cp backend/.env.example backend/.env
# .env ichida GEMINI_API_KEY yoki OPENAI_API_KEY ni kiriting
```

### 3. Ishga tushirish

Loyiha uchun tayyor skriptlar mavjud:

```bash
# Barcha xizmatlarni (Django, Celery, UzSpell, Frontend) bitta buyruq bilan ishga tushirish:
bash start_all.sh

# Faqat Celery xizmatini qayta ishga tushirish (kod o'zgarganda):
bash restart_celery.sh

# Barcha fon jarayonlarini to'xtatish:
bash kill_all_celery.sh
```

Alohida ishga tushirish:

**Backend:**
```bash
source backend/venv/bin/activate
cd backend
python manage.py runserver
```

**Celery:**
```bash
source backend/venv/bin/activate
celery -A config worker -l INFO --pool=solo
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**UzSpell Service:**
```bash
source backend/venv/bin/activate
cd uzspell
python app.py
```

---

## 📁 Loyiha Tuzilishi

```
legal-bridge-ai/
├── ai_engine/           # Asosiy AI, OCR, Parser va Risk Scoring mantiqlari
├── backend/             # Django API serveri
│   ├── apps/            # Django ilovalari (contracts, analysis, users)
│   ├── config/          # Loyiha sozlamalari
│   └── media/           # Yuklangan shartnomalar va hisobotlar
├── frontend/            # React ilovasi
├── shartnomalar/        # Test uchun shartnoma namunalari
├── uzspell/             # Imlo tekshirish mikroservisi
├── scripts/             # Yordamchi tahlil skriptlari
└── start_all.sh         # Loyihani ishga tushirish menejeri
```

---

## 🔒 Xavfsizlik va Maxfiylik

*   Barcha yuklangan fayllar mahalliy serverda qayta ishlanadi (`media` papkasi).
*   LLM (Gemini/OpenAI) ga faqat matnning anonimlashtirilgan yoki kerakli qismlari yuboriladi (agar sozlamalarda yoqilgan bo'lsa).
*   API JWT token orqali himoyalangan.

---

## 📞 Aloqa va Yordam

Loyiha bo'yicha savollar yoki takliflar bo'lsa, ishlab chiquvchilar jamoasiga murojaat qiling.

**"Ko'prikqurilish AJ" uchun maxsus ishlab chiqilgan.**
