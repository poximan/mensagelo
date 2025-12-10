FROM python:3.12-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl tzdata && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# deps primero para cache
COPY timeauthority-pkg /timeauthority-pkg
COPY mensagelo/email_service/requirements.txt /app/requirements.txt
RUN pip install --no-compile -r /app/requirements.txt

# usuario no-root
RUN useradd -m -u 10002 appsvc

# código
COPY mensagelo/email_service /app/email_service

USER appsvc

EXPOSE 8081

CMD ["python", "-m", "email_service.main"]
