# Usa Python slim
FROM python:3.11-slim

WORKDIR /

# Installa solo librerie esterne
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia tutti i file locali (app.py + moduli custom)
COPY . .

# Espone porta per Cloud Run
EXPOSE 8080

# Avvio Flask
CMD ["python", "app.py"]
