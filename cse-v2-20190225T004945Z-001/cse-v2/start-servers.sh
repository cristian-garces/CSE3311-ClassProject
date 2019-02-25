#!/bin/bash

int_check='^[0-9]+$'
PS3='Please select which server to start: '
options=("Sandbox" "Dev" "Test" "Quit")
select opt in "${options[@]}"
do
    case $opt in
        "Sandbox")
            PID="$(ps aux | grep gunicorn | grep 5004 | grep ' [RS]\{1\}+\? ' | awk '{print $2}')"
            if [[ $PID =~ $int_check ]];
            then
                echo "The cse-v2 sandbox server is already running. Please kill it before trying to start it again."
            else
                echo "Starting the cse-v2 sandbox server"
                nohup gunicorn -k gthread --threads 5 -w 7 -t 180 --max-requests 250 --reload --certfile /opt/www/certs/server.crt --keyfile /opt/www/certs/server.key --bind 0.0.0.0:5004 'app:app' & disown -h
                sleep 2
                echo -e "Done. \n"
            fi
            break
            ;;
        "Dev")
            PID="$(ps aux | grep gunicorn | grep 5003 | grep ' [RS]\{1\}+\? ' | awk '{print $2}')"
            if [[ $PID =~ $int_check ]];
            then
                echo "The cse-v2 dev server is already running. Please kill it before trying to start it again."
            else
                echo "Starting the cse-v2 dev server"
                nohup gunicorn -k gthread --threads 5 -w 7 -t 180 --max-requests 250 --reload --certfile /opt/www/certs/server.crt --keyfile /opt/www/certs/server.key --bind 0.0.0.0:5003 'app:app' & disown -h
                sleep 2
                echo -e "Done. \n"
            fi
            break
            ;;
        "Test")
            PID="$(ps aux | grep gunicorn | grep 5002 | grep ' [RS]\{1\}+\? ' | awk '{print $2}')"
            if [[ $PID =~ $int_check ]];
            then
                echo "The cse-v2 test server is already running. Please kill it before trying to start it again."
            else
                echo "Starting the cse-v2 test server"
                nohup gunicorn -k gthread --threads 5 -w 7 -t 180 --max-requests 250 --reload --certfile /opt/www/certs/server.crt --keyfile /opt/www/certs/server.key --bind 0.0.0.0:5002 'app:app' & disown -h
                sleep 2
                echo -e "Done. \n"
            fi
            break
            ;;
        "Quit")
            break
            ;;
        *) echo "Invalid option: $REPLY";;
    esac
done
