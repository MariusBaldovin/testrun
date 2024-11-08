#!/bin/bash -x

# Display network interfaces
ip a

# Set paths and servers
NTP_SERVER=10.10.10.5
DNS_SERVER="nonexistent.dns.server"
INTF=eth0

# Check if the interface is up
ip link show $INTF | grep "state UP" || echo "Warning: $INTF is not up"

# DHCP setup
ip addr flush dev $INTF
PID_FILE=/var/run/dhclient.pid
if [ -f $PID_FILE ]; then
  kill -9 $(cat $PID_FILE) || true
  rm -f $PID_FILE
fi
dhclient -v $INTF &
DHCP_TPID=$(pgrep -f "dhclient.*$INTF" | head -n 1)
echo $DHCP_TPID

## SERVICES MODULE

# Function to check if TCP service is running
check_tcp_service() {
  local service=$1
  local port=$2
  if netstat -tln | grep -q ":$port"; then
      echo "$service started on TCP port: $port"
  else
      echo "$service failed to start on TCP port $port"
  fi
}

# Function to check if UDP service is running
check_udp_service() {
  local service=$1
  local port=$2
  if ss -uln | grep -q ":$port"; then
    echo "$service started on UDP port: $port"
  else
    echo "$service failed to start on UDP port $port"
  fi
}

# Start FTP service 
echo "Starting FTP on ports 20, 21"
nc -nvlt -p 20 & sleep 3
check_tcp_service "FTP" 20
nc -nvlt -p 21 & sleep 3
check_tcp_service "FTP" 21

# Start Telnet service 
echo "Starting Telnet on port 23"
nc -nvlt -p 23 & sleep 3
check_tcp_service "Telnet" 23

# Start SMTP service
echo "Starting SMTP on ports 25, 465, and 587"
nc -nvlt -p 25 & sleep 3
check_tcp_service "SMTP" 25
nc -nvlt -p 465 & sleep 3
check_tcp_service "SMTP" 465
nc -nvlt -p 587 & sleep 3
check_tcp_service "SMTP" 587

# Start HTTP service 
echo "Starting HTTP on port 80 "
nc -nvlt -p 80 & sleep 3
check_tcp_service "HTTP" 80

# Start POP service 
echo "Starting POP on ports 109 and 110 "
nc -nvlt -p 109 & sleep 3
check_tcp_service "POP" 109
nc -nvlt -p 110 & sleep 3
check_tcp_service "POP" 110

# Start IMAP service 
echo "Starting IMAP on port 143 "
nc -nvlt -p 143 & sleep 3
check_tcp_service "IMAP" 143

# Start SNMPv2 service 
echo "Starting SNMPv2 on port 161"
(while true; do echo -ne " \x02\x01\ " | nc -u -l -w 1 161; done) & sleep 3

check_udp_service "SNMPv2" 161

# Start TFTP service 
echo "Starting TFTP on port 69 "
(while true; do echo -ne "\0\x05\0\0\x07\0" | nc -u -l -w 1 69; done) & sleep 3

# Check if TFTP is running on port 69
check_udp_service "TFTP" 69

# Start the NTP server
echo "Starting NTP service"
ntpd -g -n -d &

# Wait and verify if the NTP server is listening on UDP port 123
sleep 3

# Check if NTP is running on port 123 3

# Start VNC server

# Set default environment variables
RESOLUTION=${RESOLUTION:-1920x1080}
DISPLAY=:1
export USER=${USER:-root}

# Add hostname to /etc/hosts to avoid warnings
echo 'Updating /etc/hosts file...'
HOSTNAME=$(hostname)
echo "0.0.0.0\t$HOSTNAME" >> /etc/hosts

# Start the VNC server
echo "Starting VNC server"
vncserver :1 -geometry $RESOLUTION -rfbport 5901 &
sleep 10

if pgrep Xtightvnc >/dev/null; then
    echo "VNC server started successfully"
else
    echo "Warning: VNC server failed to start"
fi

# Capture vnc ports
VNC_PORTS=$(netstat -tlnp 2>/dev/null | grep Xtightvnc | awk '{print $4}' | cut -d: -f2)
echo "VNC server started on ports: $VNC_PORTS"

# Check VNC server on ports 5901 and 6001
netstat -tlnp | grep Xtightvnc
netstat -tlnp | grep -E '5901|6001'

## DNS MODULE

# Test DNS resolution
echo "Sending DNS request to $DNS_SERVER"
dig @$DNS_SERVER +short www.google.com || echo "DNS resolution failed"

# Keep network monitoring
(while true; do arping -i $INTF 10.10.10.1; sleep 10; done) &
(while true; do ip a | cat; sleep 10; done) &

# Keep the script running
tail -f /dev/null

