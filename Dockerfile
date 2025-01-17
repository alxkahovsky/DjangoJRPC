FROM python:3.12-slim
WORKDIR /django_app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
RUN ["python", "manage.py", "makemigrations"]
RUN ["python", "manage.py", "migrate"]