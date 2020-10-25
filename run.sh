#!/bin/bash
#######################
# Variablen ###########
#######################
name="LEDserver"
#######################
# Script ##############
#######################
case "$1" in
        start)
                tmux new -d -s ${name} "sudo python backend.py"
                echo "Server wird gestartet"
                ;;
        console)
                tmux attach -t ${name}
                ;;
	stop)
		echo "Server wird gestoppt"
		tmux kill-session -t ${name}
		;;
	update)
		echo "Server wird gestoppt"
		tmux kill-session -t ${name}
		sudo wget -O /var/www/html/index.html https://raw.githubusercontent.com/JulianSpieker/ws2812bcontrol/main/index.html
		sudo wget -O /var/www/html/frontend.js https://raw.githubusercontent.com/JulianSpieker/ws2812bcontrol/main/frontend.js
		sudo wget -O /var/www/html/style.css https://raw.githubusercontent.com/JulianSpieker/ws2812bcontrol/main/style.css
		sudo wget -O /var/www/html/increaseBrightness.svg https://raw.githubusercontent.com/JulianSpieker/ws2812bcontrol/main/increaseBrightness.svg
		sudo wget -O /var/www/html/decreaseBrightness.svg https://raw.githubusercontent.com/JulianSpieker/ws2812bcontrol/main/decreaseBrightness.svg
		sudo wget -O /home/pi/backend.py https://raw.githubusercontent.com/JulianSpieker/ws2812bcontrol/main/backend.py
		echo "Server wird gestartet"
		tmux new -d -s ${name} "sudo python backend.py"
		;;
        *)
                echo "Read The Fucking Manual ;) ${0} {start|console|stop|update}"
                exit 1
esac
exit 0
