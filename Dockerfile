FROM python:3.7-slim

ARG APP_ENV="dev"

RUN useradd -ms /bin/bash worker \
    && apt-get update \
    && apt-get install -y git
COPY requirements.txt /requirements.txt
RUN python3 -m pip install -r /requirements.txt

USER worker
WORKDIR /home/worker
ENV PYTHONPATH="${PYTHONPATH}:${HOME}"

EXPOSE 5000 5050
