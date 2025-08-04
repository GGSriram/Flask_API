FROM python:3.9-slim

WORKDIR /app

# Install dependencies for psycopg2 and clean up
RUN apt-get update \
  && apt-get install -y gcc libpq-dev \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

CMD ["flask", "run"]
