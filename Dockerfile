FROM debian:9

RUN apt -q update && \
    env DEBIAN_FRONTEND=noninteractive apt upgrade -y && \
    env DEBIAN_FRONTEND=noninteractive apt install -qy --no-install-recommends \
        python3 \
        python3-pip \
        python3-venv \
        git-core

# Add "libev4" for bjoern

RUN mkdir -p /app && \
        chown www-data:www-data /app

USER www-data

ADD --chown=www-data:www-data . /app/src
WORKDIR /app/src
RUN python3 -m venv /app/venv && \
        /app/venv/bin/pip3 install --no-cache-dir -qU pip && \
        /app/venv/bin/pip3 install --no-cache-dir -e ".[mysql]"

ENV FLASK_APP=qstode.wsgi:app \
        APP_CONFIG=/app/src/config.py \
        FLASK_ENV=development \
        LC_ALL=C.UTF-8 \
        LANG=C.UTF-8

EXPOSE 5000
ENTRYPOINT ["/app/venv/bin/python", "-m", "flask"]
CMD ["run", "-h", "0.0.0.0"]
