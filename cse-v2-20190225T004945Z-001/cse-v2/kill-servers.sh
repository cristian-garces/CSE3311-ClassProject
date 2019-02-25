#!/bin/bash

int_check='^[0-9]+$'
PS3='Please select which server to kill: '
options=("Sandbox" "Dev" "Test" "Quit")
select opt in "${options[@]}"
do
    case $opt in
        "Sandbox")
            PID="$(ps aux | grep gunicorn | grep 5004 | grep ' [RS]\{1\}+\? ' | awk '{print $2}')"
            if [[ $PID =~ $int_check ]];
            then
                echo "Killing the cse-v2 sandbox server..."
                kill $PID
                while $(kill -0 $PID 2>/dev/null); do
                    sleep 1
                done
                echo -e "Done.\n"
            else
                echo "The cse-v2 sandbox server was not found to be running."
            fi
            break
            ;;
        "Dev")
            PID="$(ps aux | grep gunicorn | grep 5003 | grep ' [RS]\{1\}+\? ' | awk '{print $2}')"
            if [[ $PID =~ $int_check ]];
            then
                echo "Killing the cse-v2 dev server..."
                kill $PID
                while $(kill -0 $PID 2>/dev/null); do 
                    sleep 1
                done
                echo -e "Done.\n"
            else
                echo "The cse-v2 dev server was not found to be running."
            fi
            break
            ;;
        "Test")
            PID="$(ps aux | grep gunicorn | grep 5002 | grep ' [RS]\{1\}+\? ' | awk '{print $2}')"
            if [[ $PID =~ $int_check ]];
            then
                echo "Killing the cse-v2 test server..."
                kill $PID
                while $(kill -0 $PID 2>/dev/null); do 
                    sleep 1
                done
                echo -e "Done.\n"
            else
                echo "The cse-v2 test server was not found to be running."
            fi
            break
            ;;
        "Quit")
            break
            ;;
        *) echo "Invalid option: $REPLY";;
    esac
done
