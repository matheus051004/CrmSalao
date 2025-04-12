# Imagem base com Python 3.10
FROM python:3.10-slim

# Definir diretório de trabalho
WORKDIR /app

# Copiar os requisitos e instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


ENV CRM_NAME="CRM BarberPRO"
ENV CRM_USER="admin"
ENV CRM_PASSWORD="admin"
ENV VERSION="1.0.3"

ENV POSTGRES_HOST="209.145.51.166"
ENV POSTGRES_PORT="5432"
ENV POSTGRES_USER="postgres"
ENV POSTGRES_PASSWORD="e3121c21-dfd5-42c3-bc74-5e71dad28c91"
ENV POSTGRES_DB="postgres"


# Copiar todo o código da aplicação
COPY . .

# Expor a porta que será usada
EXPOSE 8000

# Comando para iniciar o servidor
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]