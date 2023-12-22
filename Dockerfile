FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11-slim

LABEL maintainer="Max Mecklin <max@meckl.in>"
LABEL authors="Max Mecklin <max@meckl.in>"

COPY requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt
RUN pip install git+https://github.com/Natsku123/pygw2@master

COPY . /app

RUN date +%Y.%m.%d > .build

ENV PYTHONPATH "${PYTHONPATH}:/app"
ENV VERSION=${BUILD_VERSION}
