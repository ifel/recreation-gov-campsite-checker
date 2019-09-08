#!/bin/sh

iter () {
	# test sites 234608 234691
	date
	result=`python camping.py crawl --exit_code --only_available --html --request $REQUEST`
	avail=$?
	echo "$result"
	if [ "$avail" -eq 0 ]; then
		echo "$result" | telegram-send -g --stdin --format html
		sleep 900
	fi

	sleep 60
}

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

cat > /etc/telegram-send.conf <<END
[telegram]
token = $TELEGRAM_TOKEN
chat_id = $TELEGRAM_CHAT_ID
END

LOOKUP_INFO=$(python camping.py crawl_info --html --request $REQUEST)
echo -e "Crawler started\n$LOOKUP_INFO" | telegram-send --stdin -g --html

while :; do iter; done
