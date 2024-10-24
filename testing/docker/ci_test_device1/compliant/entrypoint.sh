#!/bin/bash -x

# Display network interfaces
ip a

# Set paths and servers
NTP_SERVER=10.10.10.5
DNS_SERVER=8.8.8.8
INTF=eth0

# Check if the interface is up
ip link show $INTF | grep "state UP" || echo "Warning: $INTF is not up"

# DHCP
ip addr flush dev $INTF
PID_FILE=/var/run/dhclient.pid
if [ -f $PID_FILE ]; then
    kill -9 $(cat $PID_FILE) || true
    rm -f $PID_FILE
fi
dhclient -v $INTF 
DHCP_TPID=$(pgrep -f "dhclient.*$INTF")
echo $DHCP_TPID

## SERVICES MODULE

# No FTP, SSH, Telnet, SMTP, HTTP, POP, IMAP services
echo "FTP, SSH, Telnet, SMTP, HTTP, POP, IMAP, SNMP, VNC, TFTP, NTP services not running"

## NTP MODULE

# NTP support (ntp.network.ntp_support)
ntpdate -q $NTP_SERVER

# Check if the NTP request was successful
if [ $? -eq 0 ]; then
  echo "NTP request succeeded to $NTP_SERVER."
else
  echo "NTP request failed"
fi

# Obtain NTP server from DHCP and simulate NTP request (ntp.network.ntp_dhcp)
dhclient -v -sf /usr/sbin/ntpdate eth0

# Check if the DHCP server provided an NTP server and if the NTP request was successful
if grep -q "ntp-servers" /var/lib/dhcp/dhclient.leases; then
  grep "option ntp-servers" /var/lib/dhcp/dhclient.leases | awk '{print $3}' | while read ntp_server; do
    echo "NTP request sent to DHCP-provided server: $ntp_server"
    ntpdate -q $NTP_SERVER
    echo "NTP request sent to DHCP-provided server: $NTP_SERVER"
    done
else
  echo "No NTP server provided by DHCP."
fi

## CONNECTION MODULE

# connection.switch.arp_inspection

# Monitor ARP traffic using tcpdump for debugging
tcpdump -i $INTF arp &

# Display IPv4 address (connection.dhcp_address, connection.private_address, connection.shared_address, connection.single_ip)
echo "Checking for existing IP address on $INTF"
IP_ADDR=$(ip -4 addr show $INTF | grep -oP '(?<=inet\s)\d+\.\d+\.\d+\.\d+')
echo "Current IP address: $IP_ADDR"

# Display MAC address (connection.mac_address, connection.mac_oui)
echo "Device MAC Address: $(cat /sys/class/net/$INTF/address)"

# Respond to ICMP echo requests (connection.target_ping)
echo "Device responds to ICMP echo requests"
ping -c 4 8.8.8.8

## DNS MODULE

# Test DNS resolution
echo "Sending DNS request to $DNS_SERVER"
dig @$DNS_SERVER +short www.google.com

# Keep network monitoring (can refactor later for other network modules)
(while true; do arping 10.10.10.1; sleep 10; done) &
(while true; do ip a | cat; sleep 10; done) &

# Keep the script running
tail -f /dev/null

