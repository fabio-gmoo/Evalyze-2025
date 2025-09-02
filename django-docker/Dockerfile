FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1

WORKDIR /app

# instalar dependencias
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r ./requirements.txt

# copiar código del proyecto
COPY . .

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

