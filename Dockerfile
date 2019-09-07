# ENVS:
# ENV START_DATE
# ENV END_DATE
# ENV CAMPS_IDS
# ENV TELEGRAM_TOKEN
# ENV TELEGRAM_CHAT_ID

FROM python:3.7
COPY . /root
WORKDIR /root
RUN pip install --upgrade pip
RUN pip install -r /root/requirements.txt
CMD ["/root/check.sh"]
