FROM python:3.12-slim

WORKDIR /app

# git: needed so propose_code_change (moni/self_dev.py) can branch/commit on
# the bind-mounted repo at /repo (see docker-compose.yml).
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/* \
    && git config --system user.email "moni@myjarvis-ai.de" \
    && git config --system user.name "Moni"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY moni ./moni

EXPOSE 8010

CMD ["uvicorn", "moni.web:app", "--host", "0.0.0.0", "--port", "8010"]
