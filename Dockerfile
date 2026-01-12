# ---------- Base Python Image ----------
FROM python:3.12.0-slim

# ---------- Environment Setup ----------
# No spaces around '=' for ENV (important)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /code

# ---------- System Dependencies ----------
# Install build tools and PostgreSQL client libs (for psycopg2, uwsgi, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# ---------- Install Python Dependencies ----------
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------- Copy Project Files ----------
COPY . .

# ---------- Default Command ----------
# uWSGI will pick Cloud Run's port automatically (http=:$(PORT)) 
# or use socket for Docker Compose based on env detection
#CMD ["uwsgi", "--ini", "/code/config/uwsgi/uwsgi.ini"]