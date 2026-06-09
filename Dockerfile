FROM python:3.11-slim

WORKDIR /app

ARG PIP_INDEX_URL=https://pypi.org/simple
ARG PIP_TRUSTED_HOST=pypi.org

COPY requirements.txt .
RUN pip install --no-cache-dir \
    --index-url "$PIP_INDEX_URL" \
    --trusted-host "$PIP_TRUSTED_HOST" \
    -r requirements.txt

COPY . .

EXPOSE 5000

RUN pip install --no-cache-dir \
    --index-url "$PIP_INDEX_URL" \
    --trusted-host "$PIP_TRUSTED_HOST" \
    gunicorn==22.0.0
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "0", "--workers", "2", \
     "--access-logfile", "-", "--error-logfile", "-", "--capture-output", \
     "main:app"]
