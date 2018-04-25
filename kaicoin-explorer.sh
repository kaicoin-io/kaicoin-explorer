#!/bin/bash
### BEGIN INIT INFO
# /etc/init.d/kaicoin-explorer.sh
#
# description: "Kaicoin Explorer"
# processname: kaicoinExplorer
# pidfile: "/var/run/kaicoinExplorer.pid"

# Provides:          kaicoinExplorer
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Example initscript
# Description:       This file should be used to construct scripts to be
#                    placed in /etc/init.d.

### END INIT INFO

# Author: Sungjoon Kim <https://github.com/method76>

# Source function library.
. /etc/rc.d/init.d/functions

start() {
    echo "Starting kaicoin-explorer"
    cd /home/explorer/
	./startmultichain.sh
	./startrethink.sh
	./startsched.sh
	./startweb.sh
    return 0
}

stop() {
    prockill kaicoinExplorer   
    return 2
}

case "$1" in
    start)
        start
    ;;
    stop)
        stop
    ;;
    restart)
        stop
        start
    ;;
    reload)
        restart
    ;;
    status)
        status kaicoinExplorer
    ;;
    *)
        echo "Usage: kaicoinExplorer [start|stop|restart|status]"
        exit 1
    ;;
esac