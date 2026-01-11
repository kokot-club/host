FROM python:3.12-alpine

RUN apk add exiftool

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install -r requirements.txt

COPY . .

ENV PYTHONPATH="/app/src" 
ENV FLASK_ENV=production

EXPOSE 8484

CMD ["gunicorn", "-b", "0.0.0.0:8484", "wsgi:app"]
