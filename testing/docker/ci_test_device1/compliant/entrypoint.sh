#!/bin/bash -x

# Display network interfaces
ip a

# Set paths and servers
OUT=/out/testrun_ci.json
NTP_SERVER=10.10.10.5
DNS_SERVER=10.10.10.4
INTF=eth0

function wout(){
    temp=${1//./\".\"}
    key=${temp:1}\"
    echo $key
    value=$2
    jq "$key+=\"$value\"" $OUT | sponge $OUT
}


dig @8.8.8.8 +short www.google.com

# DHCP
ip addr flush dev $INTF
PID_FILE=/var/run/dhclient.pid
if [ -f $PID_FILE ]; then
    kill -9 $(cat $PID_FILE) || true
    rm -f $PID_FILE
fi
dhclient -v $INTF
DHCP_TPID=$!
echo $DHCP_TPID

# Services Module

# No FTP, SSH, Telnet, SMTP, HTTP, POP, IMAP services
echo "FTP, SSH, Telnet, SMTP, HTTP, POP, IMAP, SNMP, VNC, TFTP, NTP services not running"

# Keep network monitoring (can refactor later for other network modules)
(while true; do arping 10.10.10.1; sleep 10; done) &
(while true; do ip a | cat; sleep 10; done) &

# Keep the script running
tail -f /dev/null

