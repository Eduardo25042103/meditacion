# Usa imagen base de Python
FROM python:3.11-slim

# Establece directorio de trabajo
WORKDIR /app

# Copia dependencias y las instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código
COPY . .

# Expone el puerto de FastAPI
EXPOSE 8000

# Comando para ejecutar FastAPI con recarga (ideal para dev)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
