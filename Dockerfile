# ENVS:
# ENV START_DATE
# ENV END_DATE
# ENV CAMPS_IDS
# ENV TELEGRAM_TOKEN
# ENV TELEGRAM_CHAT_ID

FROM python:3.7-alpine
COPY . /root
WORKDIR /root
RUN apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev openssl-dev python3-dev
RUN pip install --upgrade pip
RUN pip install -r /root/requirements.txt
RUN apk del .build-deps gcc musl-dev libffi-dev openssl-dev python3-dev
ENTRYPOINT ["/root/check.sh"]
