if [ $# != 1 ] ;
then
        echo "Usage: $0 <Pi IP>"
        exit 1
fi
rsync -av "pi@$1:/home/pi/lora/ssdv/" .
