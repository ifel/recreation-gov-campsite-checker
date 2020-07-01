# ENVS:
# ENV REQUEST
# ENV TELEGRAM_TOKEN
# ENV TELEGRAM_CHAT_ID

FROM python:3.8

ENV CHECK_FREQ=60
ENV DONT_RECHECK_AVAIL_FOR=900
ENV SEND_INFO_EVERY=24

COPY . /root
WORKDIR /root
RUN pip install --upgrade pip
RUN pip install -r /root/requirements.txt
CMD ["/root/check.sh"]
