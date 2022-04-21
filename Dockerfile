FROM python:3.8

ENV PYTHONPATH=${PYTHONPATH}:${PWD}

COPY . .

COPY --from=mwader/static-ffmpeg:5.0-1 /ffmpeg /usr/local/bin/
COPY --from=mwader/static-ffmpeg:5.0-1 /ffprobe /usr/local/bin/

RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -

ENV PATH="${PATH}:/root/.poetry/bin"

RUN poetry config virtualenvs.create false
RUN poetry install --no-dev

EXPOSE 8000
