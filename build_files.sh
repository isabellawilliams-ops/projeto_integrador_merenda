#!/bin/bash
# Script de build para a Vercel
echo "=== Instalando dependências ==="
python3 -m pip install -r requirements.txt

echo "=== Coletando arquivos estáticos ==="
python3 manage.py collectstatic --noinput --clear

echo "=== Executando migrações no banco Neon ==="
python3 manage.py migrate --noinput

echo "=== Carga inicial de dados caso o banco esteja vazio ==="
python3 manage.py popular_dados

echo "=== Build concluído com sucesso! ==="
