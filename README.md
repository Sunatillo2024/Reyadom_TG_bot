# Tanishuv — Telegram tanishuv boti

18+ kichik auditoriya uchun mustaqil MVP: anketa → like/pass → o'zaro match → Telegram shaxsiy chatidagi suhbat. Bot matnlari o'zbekcha, lotin yozuvida. Boshqa botdan foydalanuvchi, anketa yoki rasmlar ko'chirilmaydi.

Python 3.11 (tekshirilgan versiya: 3.11.9), aiogram 3, SQLAlchemy asyncio, PostgreSQL/asyncpg, Alembic va pydantic-settings ishlatiladi. Bot bitta processda long polling orqali ishlaydi. FastAPI, frontend, Redis, to'lov yoki bot ichidagi anonim chat yo'q.

## Lokal ishga tushirish

Quyidagi buyruqlarni loyiha ildizida bajaring. Python 3.11 o'rnatilgan bo'lishi kerak. Toza nusxada `.venv` yaratish:

```sh
python3.11 --version
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Ushbu ish papkasida Python 3.11.9 bilan `.venv` allaqachon mavjud: uni qayta yaratish shart emas. `source .venv/bin/activate` yetarli. `python --version` natijasi `Python 3.11.9` bo'lishi kerak. PyCharm'da loyiha interpretatori sifatida `.venv/bin/python`ni tanlang. Ishga tushirish va barcha tekshiruvlar shu bitta muhitdan foydalanadi.

`.env` mavjud bo'lmagan toza nusxada:

```sh
cp -n .env.example .env
```

`.env` ni matn muharririda oching. Ushbu ish papkasida bo'sh token va bo'sh admin ro'yxati bilan `.env` tayyorlangan.

```dotenv
BOT_TOKEN=
ADMIN_IDS=[]
DATABASE_URL=postgresql+asyncpg://postgres:1212@localhost:5432/ryadom_bot
LOG_LEVEL=INFO
```

PostgreSQL lokal o'rnatilgan bo'lsa, `ryadom_bot` bazasini yarating. Docker bilan tez variant:

```sh
docker compose up -d postgres
docker compose ps
```

Docker Compose varianti hostda `55432` portini ishlatadi, shuning uchun uning lokal URL'i `postgresql+asyncpg://postgres:1212@localhost:55432/ryadom_bot`. PostgreSQL'ni to'g'ridan-to'g'ri o'rnatsangiz `.env.example` dagi standart `5432` portini qoldirishingiz mumkin. `DATABASE_URL` majburiy; loyiha faqat PostgreSQL'ni qabul qiladi. Railway beradigan `postgresql://...` (yoki `postgres://...`) URL dastur tomonidan avtomatik `postgresql+asyncpg://...` formatiga o'tkaziladi.

Telegramdagi rasmiy **@BotFather** bilan `/newbot` orqali bot yarating, olgan tokeningizni `BOT_TOKEN` ga yozing. Tokenni kodga, README'ga, gitga yoki chatlarga joylamang. Token oshkor bo'lsa, BotFather orqali almashtiring. BotFather'da guruhlarga qo'shishni o'chirishingiz mumkin; dastur baribir faqat private chatda ishlaydi.

Avval `ADMIN_IDS=[]` bilan ishga tushirib, botga `/id` yuboring. Natijani `ADMIN_IDS=[SIZNING_RAQAMLI_ID]` shaklida kiriting va botni qayta ishga tushiring. Bu yerda `SIZNING_RAQAMLI_ID` matnini haqiqiy songa almashtirish kerak. `.env.example` dagi `123456789` faqat namuna. Bir nechta admin JSON ro'yxat bilan yoziladi: `[111111111,222222222]`. Username admin huquqini bermaydi.

```sh
alembic upgrade head
python -m bot.main
```

To'xtatish: `Ctrl+C`. Bo'sh yoki noto'g'ri token bot startup'ida tushunarli xabar beradi. Migratsiya va testlar Telegram tokenini talab qilmaydi. Baza startup'da avtomatik yaratilmaydi: sxemani Alembic orqali tayyorlang.

**Bir token bilan faqat bitta polling processi ishlasin.** Lokal terminal, PyCharm va VPS'da bir xil tokenni bir paytda ishga tushirmang. Conflict bo'lsa, ortiqcha processni to'xtating; boshqa ishlayotgan servis avtomatik to'xtatilmaydi. Bu talab [aiogram long polling hujjatida](https://docs.aiogram.dev/en/latest/dispatcher/long_polling.html) ham qayd etilgan.

## Foydalanish

`/start` yangi foydalanuvchidan 18+ tasdig'i, rozilik va Telegram username talab qiladi. Keyin ism (2–40), yosh (18–99), jins, kimni qidirishi, Telegram geolokatsiyasi, ixtiyoriy tavsif (300 gacha), bitta Telegram photo va yakuniy tasdiq olinadi. Yosh foydalanuvchining bayonoti; hujjat orqali verifikatsiya qilinmaydi. Username qo'lda yozdirilmaydi.

Anketa faqat tasdiqlangach bazaga yoziladi. Qidiruv har ikki tomonning yosh va jins talablarini hisobga oladi. Ikkala foydalanuvchida geolokatsiya bo'lsa, mos anketalar Haversine masofasi bo'yicha eng yaqinidan boshlab ko'rsatiladi; qidiruv radius bilan cheklanmaydi, shuning uchun yaqin odam bo'lmasa uzoqroq profillar ham navbatda chiqadi. Eski shahar bilan yaratilgan profil geolokatsiya yuborilmaguncha faqat boshqa eski profil bilan moslashadi.

Asosiy menyu:

- 🔎 Anketalarni ko'rish — bir safar bitta rasmli anketa, eng yaqinidan uzoqrog'iga saralash, like/pass, bloklash va shikoyat.
- 👤 Mening anketam — alohida maydonlarni tahrirlash, yashirish/faollashtirish va o'chirish.
- ❤️ Menga like bosganlar — javob kutayotgan, hali ham mos va faol anketalar.
- 🤝 Matchlarim — bazadagi matchlar, har sahifada beshtadan, kontakt/blok/shikoyat.
- ⚙️ Qidiruv sozlamalari — yosh oralig'i, geolokatsiyani yangilash va qidirilayotgan jins.
- ❓ Yordam — qoidalar va komandalar.

`/help`, `/privacy`, `/cancel`, `/id`, `/delete` mavjud. `/id` faqat so'rovchining ID'sini ko'rsatadi. `/cancel` har bosqichda tugallanmagan amalni to'xtatadi. Tahrirda bitta to'g'ri qiymat yuborilishi bilan o'zgarish saqlanadi; undan oldin bekor qilish eski anketani o'zgartirmaydi. Menyuga o'tish tugallanmagan formani bekor qiladi.

O'zaro like bitta match yaratadi. Bir juftlikdagi eski qaror almashtirilmaydi; bir tomon pass qilsa juftlik qayta taklif qilinmaydi. Like/pass uchun taxminan bir soniyalik cooldown bor. Birinchi like va yangi matchdan keyingina bildirishnoma yuboriladi.

Kontakt oddiy anketada ko'rsatilmaydi. Match ishtirokchisi «Kontaktni ko'rsatish»ni bosganda ban/block/o'chirish holati tekshiriladi, kontakt egasining Telegram ID'si bilan `getChat` chaqiriladi va joriy username orqali havola tuziladi. API xatosi yoki username yo'qligida eski havola berilmaydi; qayta urinish tugmasi chiqadi. API so'rovidan keyin ruxsat yana tekshiriladi. Username keyinchalik yana o'zgarishi mumkin; ilgari yuborilgan havolaning kelajakdagi egasini kafolatlab bo'lmaydi.

Yashirilgan anketa qidiruv va kiruvchi like ro'yxatida chiqmaydi, yangi like yubormaydi; eski matchlardan foydalanish mumkin. Username olib tashlangani yoki bot bloklangani aniqlansa profil yashiriladi. Foydalanuvchi qaytgach «Mening anketam → Qayta faollashtirish»ni o'zi bosadi. Unban ham avtomatik e'lon qilmaydi.

## Maxfiylik va moderatsiya

Ochiq profil matnida `@username`, Telegram havolalari va aniq URLlar rad etiladi. Bu kontaktni yashirishga urinadigan barcha usullarni aniqlovchi tizim emas; admin moderatsiyasi kerak. Bot telefon, parol, pasport va aniq manzil so'ramaydi. Rasmlar diskka yuklanmaydi, faqat Telegram `file_id` saqlanadi. Boshqa bot tokeniga ko'chirilganda eski `file_id`lar ishlashi kafolatlanmaydi.

Shikoyat sabablari: spam, soxta profil, nomaqbul kontent, boshqa. «Boshqa» uchun 1–300 belgili izoh yoziladi. Tasdiqlangan shikoyat nishonni shikoyatchi uchun bloklaydi; bir juftlikka bittadan ochiq report saqlanadi. Shikoyatchi kimligi nishonga yuborilmaydi. Block faqat botdagi ko'rinish va kontaktga ta'sir qiladi; Telegram shaxsiy chatini alohida bloklash kerak. MVP'da blockni qaytarish tugmasi yo'q.

Admin `/admin` orqali statistika va sahifalangan shikoyatlarni ochadi, joriy anketani ko'radi, ban/unban qiladi va reportni ko'rib chiqilgan deb belgilaydi. `/ban Telegram_ID` va `/unban Telegram_ID` ham ishlaydi. Har buyruq/callbackda `ADMIN_IDS` qayta tekshiriladi. Reportda tarixiy rasm yoki anketa nusxasi saqlanmaydi: admin ayni paytdagi anketani ko'radi. Adminlar shikoyatlar ro'yxatini muntazam tekshirishi kerak; ularga ommaviy xabar yoki push navbati qo'shilmagan.

Ban oddiy amallar va eski tugmalarga ham ta'sir qiladi. Banlangan odamda yordam, maxfiylik, o'z ID'si va anketasini o'chirish imkoniyati qoladi.

O'chirish alohida tasdiq talab qiladi. Quyidagilar o'chiriladi:

- Profil: ism, yosh, jins, kimni qidirishi, shahar va normallashtirilgan shahar, bio, rasm `file_id`, yosh/shahar filtrlari, faol holat, rozilik va yangilanish vaqtlari.
- Shu foydalanuvchiga kelgan va undan ketgan barcha reaction va matchlar.
- `User.username` qiymati; keyingi Telegram update'da yana yangilanishi mumkin.

Moderatsiya uchun quyidagilar qoladi:

- `User`: ichki ID, Telegram ID, ban holati, akkaunt yaratilgan UTC vaqt.
- `Block`: yozuv ID'si, blocker va blocked ichki ID'lari, UTC vaqt.
- `Report`: yozuv ID'si, reporter va nishon ichki ID'lari, sabab/izoh, pending/reviewed holati, UTC vaqt, ko'rib chiqqan adminning ichki ID'si.

Bu qoldiriladigan ma'lumotlar o'chirishdan oldin botda tushuntiriladi. Eski Telegram xabarlari, boshqa odam allaqachon ko'rgan kontaktlar va oldingi zaxira nusxalari avtomatik yo'qolmaydi. DB va backuplarga kirishni cheklang; operator zaxira nusxalarini saqlash muddatini belgilashi kerak. Backup qayta tiklansa undagi eski holat qaytishini hisobga oling.

## Saqlash va ishlash cheklovlari

Tayyor anketalar, reaction, match, block va reportlar PostgreSQL bazasida. Har service amali alohida `AsyncSession` ochadi; umumiy global session yo'q. Engine kichik servis uchun `pool_size=5`, `max_overflow=5` va `pool_pre_ping` bilan sozlangan. Vaqtlar timezone-aware UTC sifatida saqlanadi. Telegram ID `BigInteger`; juftliklarga unique va self-action cheklovlari, profil yoshiga DB cheklovlari bor.

Like va match yaratish bitta PostgreSQL tranzaksiyasida bajariladi. Juftlik bo'yicha transaction-level advisory lock hamda `UNIQUE`/`ON CONFLICT` bir vaqtdagi takroriy reaction yoki matchni oldini oladi. Block va ochiq reportlar ham DB unique constraintlari orqali deduplikatsiya qilinadi. Telegram xabarlari commitdan keyin, DB session ushlab turilmagan holatda yuboriladi. Long polling sababli **bitta bot processi** ishlating; bir token uchun ko'p replica yoqmang.

Kichik auditoriya uchun polling update'lari ketma-ket qayta ishlanadi; Telegramning sekin javobi navbatdagi update'ni kechiktirishi mumkin. FSM'da foydalanuvchi amallari izolyatsiyasi ham bor. Oddiy yuborishlar avtomatik takrorlanmaydi. Polling tarmoq xatosida ko'pi bilan besh ketma-ket urinish qiladi; keyin process xato bilan tugaydi. `RetryAfter` bir daqiqadan katta bo'lsa ham process tugaydi. systemd cheklangan qayta ishga tushirishni boshqaradi.

Bildirishnoma «aynan bir marta yetishi» kafolatlanmaydi: commit va yuborish orasida process to'xtashi yoki tarmoq uzilishi mumkin. Alohida outbox/ish navbati yo'q. Saqlangan like va matchlar menyudan ochiladi. Takroriy tugma yangi reaction/match yoki odatiy takroriy bildirishnoma yaratmaydi.

**MemoryStorage faqat tugallanmagan forma uchun. Restartda forma, tasdiq bosqichi va cooldown yo'qoladi.** Saqlangan anketa buzilmaydi; `/start` qayta ro'yxatdan o'tishga majburlamaydi. Bu [aiogram MemoryStorage xususiyati](https://docs.aiogram.dev/en/v3.22.0/dispatcher/finite_state_machine/storages.html) va ushbu MVP'ning ongli soddalashtirishidir.

Token va profil matnlari logga yozilmaydi; kutilmagan xatolarda exception turi va kod joylari yoziladi. `.env`, `.venv*`, eski SQLite DB/WAL/SHM fayllari va backuplar `.gitignore` orqali chiqarilgan.

## Tekshiruvlar

```sh
python -m pip install -r requirements-dev.txt
docker compose exec -T postgres createdb -U postgres ryadom_bot_test
TEST_DATABASE_URL=postgresql+asyncpg://postgres:1212@localhost:55432/ryadom_bot_test pytest
ruff check .
DATABASE_URL=postgresql+asyncpg://postgres:1212@localhost:55432/ryadom_bot alembic check
```

Ruff faqat dev dependency. Versiyalar requirements fayllarida aniq qayd etilgan. Integratsion testlar xavfsizlik uchun nomi `_test` bilan tugaydigan alohida PostgreSQL bazasini va `TEST_DATABASE_URL`ni talab qiladi; sxema testlar davomida tozalanadi. Haqiqiy Telegram API chaqiruvlari mock qilinadi.

Testlar: yosh va kontakt validatsiyasi, tasdiqlanmagan profil, ikki tomon filtrlari, yashirish/ban/block/pass, takroriy va bir vaqtdagi likelar, kontakt ruxsati va joriy username, API kutishidagi ban/block/delete, notification xatolari, o'chirish va moderatsiya yozuvlari, restartdan keyingi saqlanish, toza migratsiya, bo'sh token hamda haqiqiy aiogram router/FSM orqali ro'yxatdan o'tishdan kontaktgacha bo'lgan offline oqim.

Haqiqiy token bilan qo'lda 2–3 test akkauntida tekshiring:

1. A va B akkauntlarida username bo'lsin. Botni ikkalasida `/start` qiling, 18+ va rozilikni bosing, bir xil shahar va bir-biriga mos jins/filtrlar bilan anketalarni tasdiqlang.
2. A → B like yuborsin. B'da bildirishnoma va «Menga like bosganlar»ni tekshiring. A'ning eski like tugmasini yana bosganda qaror o'zgarmasin.
3. B → A like yuborsin. Ikkalasida «Matchlarim» va «Kontaktni ko'rsatish»ni oching; havola kerakli shaxsiy chatga olib borsin.
4. B username'ini o'zgartiring yoki olib tashlang. Kontaktni yana ochib joriy havola yoki «Kontakt hozircha mavjud emas»ni tekshiring.
5. C akkaunti bilan begona matchga kontakt ochilmasligini tekshiring. Yashirish, block, report, admin ban va `/delete`ni sinang; bloklangan/banlangan/o'chirilgan profildan kontakt berilmasin.
6. Botni to'xtatib qayta ishga tushiring. Tayyor anketalar va matchlar qolsin; tugallanmagan forma yangidan boshlansin. Botni Telegramda bloklab, keyin qaytib kelganda profilni qo'lda faollashtiring.

Haqiqiy Telegram tarmog'i, haqiqiy `file_id` va BotFather sozlamalari avtomatik testlarda tekshirilmaydi.

## Railway

Railway project ichida ikkita alohida service yarating: bot repository service va PostgreSQL service. Bot service Variables bo'limida quyidagilar bo'lsin:

```dotenv
BOT_TOKEN=<BotFather tokeni>
ADMIN_IDS=[123456789]
DATABASE_URL=${{Postgres.DATABASE_URL}}
LOG_LEVEL=INFO
```

`Postgres` — PostgreSQL service nomi; boshqa nom tanlangan bo'lsa reference nomini ham moslang. Railway'ning oddiy `postgresql://...` qiymati avtomatik asyncpg URL'ga aylantiriladi. Maxfiy qiymatlarni repository yoki Docker image ichiga yozmang.

- Pre-deploy Command: `alembic upgrade head`
- Start Command: `python -m bot.main`

Bot service replica sonini **1** qilib qoldiring. Bir xil token bilan bir vaqtda lokal botni va Railway botini ham ishga tushirmang: Telegram long polling ikkinchi processga conflict qaytaradi. Deploy logida avval migratsiya muvaffaqiyatli tugaganini, keyin polling boshlanganini tekshiring.

Bu o'tishda SQLite'dan data migration ataylab qilinmadi: loyiha bazasida ko'chiriladigan real foydalanuvchi, anketa, like yoki match yo'q. Eski `data/bot.db` o'chirilmaydi va lokal backup sifatida qoladi; dastur undan boshqa foydalanmaydi.

## Linux VPS va systemd

Server allaqachon mavjud, Python 3.11 o'rnatilgan deb olinadi. Quyidagi buyruqlar **namuna**; tayyorlash vaqtida serverda bajarilmagan. Root bilan botni ishga tushirmang. Debian/Ubuntu uchun alohida xizmat foydalanuvchisi va `/opt/tanishuv`:

```sh
sudo useradd --system --user-group --home-dir /opt/tanishuv --shell /usr/sbin/nologin tanishuv
sudo install -d -o tanishuv -g tanishuv /opt/tanishuv
```

Loyiha fayllarini `/opt/tanishuv` ichiga joylashtiring. Lokal `.env`, `.venv` yoki ish bazasini tasodifan ko'chirmang. Serverda yangi `.env` tayyorlang va token/adminlarni kiriting. Fayllar xizmat foydalanuvchisi o'qiy oladigan bo'lsin:

```sh
cd /opt/tanishuv
sudo chown -R tanishuv:tanishuv /opt/tanishuv
sudo -u tanishuv python3.11 -m venv /opt/tanishuv/.venv
sudo -u tanishuv /opt/tanishuv/.venv/bin/python -m pip install -r requirements.txt
sudo -u tanishuv cp -n .env.example .env
sudo -u tanishuv nano .env
sudo chmod 600 .env
sudo -u tanishuv /opt/tanishuv/.venv/bin/alembic upgrade head
sudo install -m 644 deploy/tanishuv-bot.service /etc/systemd/system/tanishuv-bot.service
sudo systemctl daemon-reload
sudo systemctl enable --now tanishuv-bot
sudo systemctl status tanishuv-bot
```

`deploy/tanishuv-bot.service` ichidagi user, group, working directory va Python yo'lini haqiqiy joylashuvingizga moslang. `.env` pydantic-settings orqali working directory'dan o'qiladi. PostgreSQL alohida service bo'lishi va bot serveridan ulanishga ruxsat berishi kerak.

```sh
sudo systemctl restart tanishuv-bot
sudo journalctl -u tanishuv-bot -n 100 --no-pager
sudo journalctl -u tanishuv-bot -f
sudo systemctl stop tanishuv-bot
```

Startup token/baza xatosi yoki polling konflikti exit code 2 beradi; servis bunday holatda avtomatik restart qilmaydi. Boshqa xatolarda 10 soniyadan keyin restart, besh daqiqada ko'pi bilan besh start. Sabab tuzatilgach zarur bo'lsa `sudo systemctl reset-failed tanishuv-bot` va `sudo systemctl start tanishuv-bot` bajaring.

## Backup

Production PostgreSQL uchun Railway backup siyosati yoki odatiy `pg_dump`/`pg_restore` jarayonidan foydalaning. Backup faylini repositoryga qo'shmang va tiklashni alohida test bazasida muntazam tekshiring. Eski SQLite fayli faqat migratsiyadan oldingi lokal backup bo'lib qoladi.

## Asosiy fayllar va manbalar

`bot/main.py` — polling va shutdown; `bot/config.py` — `.env`; `bot/db/` — schema/ulanish; `bot/services/` — tranzaksiyalar, qidiruv, moderatsiya, Telegram xatolari; `bot/handlers/` — foydalanuvchi/admin oqimlari; `bot/keyboards/`, `bot/states.py`, `bot/texts.py` — interfeys; `bot/middlewares/` — private-chat, ban, username va cooldown; `alembic/` — migratsiyalar; `tests/` — offline tekshiruvlar; `deploy/` — xizmat namunasi.

Texnik qarorlar uchun rasmiy manbalar: [SQLAlchemy asyncpg](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#module-sqlalchemy.dialects.postgresql.asyncpg), [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/), [Railway PostgreSQL](https://docs.railway.com/guides/postgresql), [Telegram Bot API](https://core.telegram.org/bots/api). Biznes qoidalari ushbu loyiha talablari asosida yozilgan.
