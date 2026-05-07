FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends bash curl ca-certificates gnupg gpgv \
 && curl -Ls --retry 3 --retry-delay 2 https://cli.doppler.com/install.sh -o /tmp/doppler-install.sh \
 && bash /tmp/doppler-install.sh --no-confirm \
 && rm /tmp/doppler-install.sh \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

