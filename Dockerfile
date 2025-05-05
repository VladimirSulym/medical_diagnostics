FROM python:latest
WORKDIR /habit_tracker

COPY requirements.txt .
RUN pip install gunicorn
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
