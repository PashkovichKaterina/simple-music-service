FROM python:3.8

ENV PYTHONPATH=${PYTHONPATH}:${PWD}

COPY . .

RUN pip3 install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev

