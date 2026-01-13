# Dockerfile para Railway - NFS-e Automation System
FROM python:3.11-slim

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libssl-dev \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Define diretório de trabalho
WORKDIR /app

# Copia requirements primeiro (para cache de layers)
COPY requirements.txt .

# Instala dependências Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia o resto do código
COPY . .

# Cria diretório para certificados, converte line endings e ajusta permissões
RUN mkdir -p certificados && \
    dos2unix start.sh && \
    chmod +x start.sh

# Expõe a porta (Railway define PORT automaticamente)
EXPOSE 8501

# Comando de inicialização
ENTRYPOINT ["/bin/bash", "start.sh"]
