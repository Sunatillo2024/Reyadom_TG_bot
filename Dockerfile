# Python bazaviy imidj
FROM python:3.11-slim

# Ishchi katalog
WORKDIR /app

# Kutubxonalarni o‘rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kodni konteynerga nusxalash
COPY . .

# Muhit o‘zgaruvchilarni sozlash (agar kerak bo‘lsa)
ENV PYTHONUNBUFFERED=1

# Botni ishga tushirish
CMD ["python", "-m", "bot.main"]
