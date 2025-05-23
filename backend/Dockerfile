# Usa imagen base de Python
FROM python:3.11-slim

# Establece directorio de trabajo
WORKDIR /app

#Intala dependencias para PostgresqL
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*
    
# Copia dependencias y las instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código
COPY . .

# Expone el puerto de FastAPI
EXPOSE 8000

# Comando para ejecutar FastAPI con recarga (ideal para dev)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
