#!/bin/sh

function iter {
	# test sites 234608 234691
	date
	result=`python camping.py --start-date $START_DATE --end-date $END_DATE --no_overall --exit_code --only_available $CAMPS_IDS`
	avail=$?
	echo "$result"
	if [ "$avail" -eq 0 ]; then
		echo "$result" | sed -E -e 's/^([^ ]+ )([^\(]+)\(([0-9]+)(\):.*)/\1<a href="https:\/\/www.recreation.gov\/camping\/campgrounds\/\3\/availability">\2<\/a>(\3\4/g' | telegram-send -g --stdin --format html
		sleep 900
	fi

	sleep 60
}

if [ -z "$START_DATE" ]; then
	echo "ENV START_DATE var was not provided"
	exit 62
fi

if [ -z	"$END_DATE" ]; then
	echo "ENV END_DATE var was not provided"
	exit 63
fi

if [ -z "$CAMPS_IDS" ]; then
	echo "ENV CAMPS_IDS var was not provided"
	exit 64
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

echo "Crawler started to find a place from $START_DATE to $END_DATE in $CAMPS_IDS" | telegram-send --stdin -g

while :; do iter; done
