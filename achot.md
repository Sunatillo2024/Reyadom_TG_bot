# Tanishuv bot — Premium tizimi va yangilanishlar hisoboti

Hisobot sanasi: 2026-09-21  
Loyiha: **"Рядом" Telegram Tanishuv Boti**  
Arxitektura: Python 3.11, aiogram 3.22, PostgreSQL 16, SQLAlchemy 2.0 Asyncio, Alembic

---

## 🌟 Umumiy qisqacha mazmun

Botga to‘liq **Free (bepul)** va **Premium (pullik obuna)** tizimi ishlab chiqildi va integratsiya qilindi. Foydalanuvchilar uchun qulay obuna tariflari, cheklovlar va eksklyuziv funksiyalar yaratildi. Ma’lumotlar bazasi PostgreSQL va SQLAlchemy orqali kengaytirilib, 100% testlar bilan qamrab olindi.

---

## 💎 Free vs Premium funksiyalari taqqosi

| Imkoniyat | 🆓 Free (Oddiy) | 💎 Premium |
|---|:---:|:---:|
| **Kunlik Like limiti** | Kuniga 30 ta like (har kuni 00:00 UTC da yangilanadi) | **Cheksiz** layklar |
| **Anketani qaytarish (⏪ Вернуть)** | Kuniga 1 marta | **Cheksiz** anketani orqaga qaytarish |
| **Profil rasmlari soni** | 1 ta asosiy rasm | **5 tagacha** rasm (interaktiv galereya) |
| **Profilni ko‘tarish (🚀 Boost)** | Mavjud emas | **30 daqiqalik Boost** (24 soatlik cooldown) |
| **Premium belgisi (💎 Badge)** | Mavjud emas | Profil va kartada **💎 nishoni** (yoqish/o‘chirish mumkin) |
| **Qidiruv radiusi** | Faqat eng yaqinlari / bitta shahar | **10, 25, 50, 100 km yoki Cheksiz** radius filtri |
| **Kiruvchi layklar (❤️ Мне поставили лайк)** | Ko‘rish va javob qaytarish mumkin | Ko‘rish va javob qaytarish mumkin |

---

## 📦 Obuna tariflari (Tariff Plans)

Barcha obuna muddatlari UTC vaqt mintaqasi va taqvimiy oylar asosida aniq hisoblanadi:

1. **`premium_3d` (3 kunlik sinov)**
   - Narxi: 200 Telegram Stars / Admin orqali
   - Davomiyligi: 72 soat (3 kun)
2. **`premium_1m` (1 oylik obuna)**
   - Narxi: 500 Telegram Stars
   - Davomiyligi: 1 kalendar oyi (`dateutil.relativedelta(months=1)`)
3. **`premium_3m` (3 oylik obuna - foydali)**
   - Narxi: 1200 Telegram Stars (20% tejash)
   - Davomiyligi: 3 kalendar oyi (`relativedelta(months=3)`)

> **Obunani uzaytirish (Stacking):** Foydalanuvchi faol obunasi tugamasdan yana obuna sotib olsa, yangi muddat avvalgi obunaning tugash sanasiga qo‘shiladi.

---

## 🛠 Texnik arxitektura va o‘zgarishlar

### 1. Ma’lumotlar bazasi (Alembic `0004_add_premium_system.py`)

Quyidagi yangi jadvallar va ustunlar qo‘shildi:
- **`users`**:
  - `premium_until` (`DateTime(timezone=True)`) — obuna tugash vaqti (NULL bo‘lsa — Free).
  - `show_premium_badge` (`Boolean`, default True) — 💎 nishonini ko‘rsatish/yashirish sozlamasi.
- **`profiles`**:
  - `search_radius` (`Integer`, default NULL) — Premium foydalanuvchilar uchun moslashtirilgan radius (km).
- **`profile_photos`**:
  - Profil uchun 5 tagacha qo‘shimcha rasmlar galereyasi (`id`, `user_id`, `photo_file_id`, `position`, `created_at`).
- **`profile_boosts`**:
  - Profilni yuqoriga ko‘tarish logi (`user_id`, `started_at`, `ends_at`, `next_available_at`).
- **`premium_grants`**:
  - Admin tomonidan berilgan va bekor qilingan obunalar auditi (`admin_user_id`, `target_user_id`, `plan`, `granted_at`, `expires_at`, `revoked_at`).

### 2. Dasturiy modullar

- **`bot/services/premium.py`**:
  - Obuna muddatini hisoblash (`calculate_premium_end`), Premium holatini tekshirish (`has_premium`), layk limitlarini tekshirish (`can_send_like`), rasm limitlari (`photo_limit`) va vaqt hisoblash funksiyalari.
- **`bot/handlers/premium.py`**:
  - Premium menyusi, ta’riflar ko‘rinishi, rasmlar galereyasini boshqarish (qo‘shish/o‘chirish), Boost faollashtirish va nishonni boshqarish handlerlari.
- **`bot/handlers/discovery.py`**:
  - Anketalarni ko‘rishda ko‘p rasmli galereyani varaqlash (`◀️ 1/5 ▶️`), `edit_message_media` orqali chatni ifloslantirmasdan rasmlarni almashtirish va o‘tkazib yuborilgan anketani orqaga qaytarish (`undo:pass`).
- **`bot/services/store.py`**:
  - Qidiruv algoritmi Boost qilingan profillarni eng birinchi o‘ringa qo‘yadi.
  - Bir paytning o‘zida bo‘ladigan layklar uchun PostgreSQL tranzaksiyalari va `pg_advisory_xact_lock` qulflari orqali deadlock va connection pool muammolari to‘liq bartaraf etildi.

### 3. Administrator komandalari

Adminlar uchun Premium boshqaruvi:
- `/premium_grant <telegram_id> <premium_3d|premium_1m|premium_3m>` — foydalanuvchiga Premium berish.
- `/premium_status <telegram_id>` — foydalanuvchining Premium holati va qolgan muddatini ko‘rish.
- `/premium_revoke <telegram_id>` — foydalanuvchidan Premium obunani olib tashlash (audit jadvalida qayd etiladi).

---

## 🧪 Sinov va Tekshiruv Natijalari (Tests & QA)

Loyihadagi barcha biznes mantiq va Telegram oqimlari avtomatlashtirilgan testlar bilan tekshirildi:

- **Pytest natijasi:** `63 passed` (100% muvaffaqiyatli).
  - `tests/test_premium.py` — Premium tariflari, stacking, boost cooldown, galereya limitlari, admin grant/revoke testlari.
  - `tests/test_telegram_flow.py` — Telegram interfeysi, discovery, FSM va tugmalar integratsiya testlari.
  - `tests/test_business.py` — Matching algoritmi, masofa va yosh bo‘yicha filtrlash testlari.
  - `tests/test_migrations_startup.py` — Alembic migratsiyasi va bazaning to‘liq mosligi.
- **Linter va Formatlash:** `ruff check .` — xatoliklar yo‘q, barcha importlar tartiblangan.
- **Baza sinxronligi:** `alembic check` — barcha modellar migratsiya bilan 100% mos.

---

## 📁 Loyihaning asosiy fayllar tarkibi

| Fayl | Tavsifi |
|---|---|
| `bot/services/premium.py` | Premium obunaning asosiy biznes qoidalari va yordamchi funksiyalari |
| `bot/handlers/premium.py` | Premium menyusi, rasmlar galereyasi va boost handlerlari |
| `bot/services/store.py` | Baza bilan ishlash, qidiruv algoritmi, boost prioriteti va tranzaksiyalar |
| `bot/handlers/discovery.py` | Anketalarni ko‘rsatish, galereya navigatsiyasi va layk/pass jarayoni |
| `bot/handlers/admin.py` | Admin boshqaruvi va `/premium_*` komandalari |
| `alembic/versions/0004_*.py` | Premium tizimi uchun PostgreSQL migratsiyasi |
| `tests/test_premium.py` | Premium funksiyalari uchun to‘liq test to‘plami |
| `.gitignore` & `.dockerignore` | Docker va Git uchun optimallashtirilgan chiqarib tashlash qoidalari |
