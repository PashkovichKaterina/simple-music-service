FROM python:3.8

ENV PYTHONPATH=${PYTHONPATH}:${PWD}

COPY . .

RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -

ENV PATH="${PATH}:/root/.poetry/bin"

RUN poetry config virtualenvs.create false
RUN poetry install --no-dev

