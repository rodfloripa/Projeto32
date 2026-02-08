# Usando uma imagem Python leve mas completa
FROM python:3.9-slim

# Define o diretório de trabalho
WORKDIR /app

# Instala dependências do sistema necessárias para o sentencepiece e torch
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia os arquivos de código para o container
COPY vector_service.py llm_service.py inference.py requirements.txt ./

# Instala as dependências do Python
# Usamos o pip install com flags para evitar cache e economizar espaço na imagem
RUN pip install --no-cache-dir -r requirements.txt

# Criamos o script de inicialização (start.sh)
# Ele sobe o Vector, espera, sobe o LLM, espera e então inicia o Gunicorn
RUN echo '#!/bin/bash\n\
echo "### [Sistema] Iniciando Microserviços..." \n\
python3 -u vector_service.py & \n\
sleep 15 \n\
python3 -u llm_service.py & \n\
sleep 45 \n\
echo "### [Sistema] Iniciando Orquestrador Gunicorn..." \n\
exec gunicorn -b 0.0.0.0:8080 --timeout 300 --workers 1 --log-level debug inference:app \n\
' > /app/start.sh

# Dá permissão de execução ao script
RUN chmod +x /app/start.sh

# Expondo a porta que o SageMaker utiliza
EXPOSE 8080

# Comando para iniciar o container
ENTRYPOINT ["/app/start.sh"]
