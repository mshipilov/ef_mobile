FROM python:3.12-slim

WORKDIR /ef_mobile

COPY app/*.py ./app/
COPY .env requirements.txt .

RUN pip install -r requirements.txt
