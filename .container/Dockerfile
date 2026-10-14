FROM python:3.12-slim

WORKDIR /app

COPY .container/app.py        /app/app.py
COPY .container/supervisor.py /app/supervisor.py

RUN groupadd -r -g 10001 sovereign \
 && useradd  -r -u 10001 -g sovereign -d /app -s /usr/sbin/nologin sovereign \
 && mkdir -p /var/lib/sovereign \
 && chown -R sovereign:sovereign /app /var/lib/sovereign

USER sovereign

ENV HOST=0.0.0.0 \
    PORT=380 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    STATE_DIR=/var/lib/sovereign

EXPOSE 380

ENTRYPOINT ["python3", "/app/supervisor.py", "python3", "/app/app.py"]
