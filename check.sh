#!/bin/sh

if [ -z "$REQUEST" ]; then
	echo "ENV var REQUEST was not provided"
	exit 62
fi

if [ -z "$TELEGRAM_TOKEN" ]; then
	echo "ENV TELEGRAM_TOKEN var was not provided"
	exit 65
fi

if [ -z "$TELEGRAM_CHAT_ID" ]; then
	echo "ENV TELEGRAM_CHAT_ID var was not provided"
	exit 66
fi

python camping.py crawl_loop --exit_code --only_available --html --request $REQUEST --telegram_token "$TELEGRAM_TOKEN" --telegram_chat_id "$TELEGRAM_CHAT_ID" --check_freq $CHECK_FREQ --dont_recheck_avail_for $DONT_RECHECK_AVAIL_FOR --send_info_every $SEND_INFO_EVERY
