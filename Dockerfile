FROM python:3.12

# Instala o Nginx
RUN apt-get update && apt-get install nginx --yes

# Copia os requisitos do projeto
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY deploy/prod-requirements.txt prod-requirements.txt
RUN pip install --no-cache-dir -r prod-requirements.txt

# Copia o arquivo de configuração do Nginx
COPY deploy/nginx.conf /etc/nginx/sites-enabled/default

# Copia todos os arquivos do projeto para o contêiner
COPY . app
WORKDIR /app

# Adiciona permissão de execução ao entrypoint.sh
RUN chmod +x /app/deploy/entrypoint.sh

# Expondo a porta 8080
EXPOSE 8080

# Comando de inicialização do contêiner
CMD ["/app/deploy/entrypoint.sh"]
