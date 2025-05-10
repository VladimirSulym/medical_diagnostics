FROM python:latest
WORKDIR /medical_diagnostics


RUN apt-get update && apt-get install -y locales \
    && localedef -i ru_RU -c -f UTF-8 -A /usr/share/locale/locale.alias ru_RU.UTF-8
ENV LANG ru_RU.UTF-8
ENV LC_ALL ru_RU.UTF-8

RUN pip install gunicorn
RUN pip install poetry
COPY pyproject.toml /medical_diagnostics/
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-root

COPY . /medical_diagnostics


