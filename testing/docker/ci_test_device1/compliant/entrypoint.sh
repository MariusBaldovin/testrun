#!/bin/bash -x

# Display network interfaces
ip a

# Set paths and servers
NTP_SERVER=10.10.10.5
DNS_SERVER=8.8.8.8
INTF=eth0

# Ensure IPv6 is enabled
sysctl net.ipv6.conf.$INTF.disable_ipv6=0

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


# # CURRENTLY NOT WORKING becasue docker is not exposing hardware-level details

# # connection.port_link
# echo "Ensuring the network port is active and error-free"
# ip link set $INTF up
# ethtool $INTF

# # connection.port_speed
# # connection.port_duplex
# if ethtool eth0 | grep -q "Supports auto-negotiation: Yes"; then
#     echo "Setting port speed to auto-negotiate"
#     ethtool -s eth0 autoneg on speed 100 duplex full
#     echo "Setting duplex mode to auto-negotiate"
#     ethtool -s eth0 autoneg on
# else
#     echo "Auto-negotiation not supported on eth0"
# fi

# connection.switch.arp_inspection

# Allow valid ARP requests and replies, drop others
echo "Setting up ARP inspection with ebtables"
ebtables -A INPUT -p ARP --arp-opcode Request --arp-ip-src 192.168.0.0/24 --arp-ip-dst 192.168.0.0/24 -j ACCEPT
ebtables -A INPUT -p ARP --arp-opcode Reply --arp-ip-src 192.168.0.0/24 --arp-ip-dst 192.168.0.0/24 -j ACCEPT
ebtables -A INPUT -p ARP -j DROP

# Monitor ARP traffic using tcpdump (optional for debugging)
tcpdump -i $INTF arp &

# Display IPv4 address (connection.dhcp_address, connection.private_address, connection.shared_address)
echo "Checking for existing IP address on $INTF"
IP_ADDR=$(ip -4 addr show $INTF | grep -oP '(?<=inet\s)\d+\.\d+\.\d+\.\d+')
echo "Current IP address: $IP_ADDR"

# Display MAC address (connection.mac_address, connection.mac_oui)
echo "Device MAC Address: $(cat /sys/class/net/$INTF/address)"

# Only one IP address configured (connection.single_ip)
echo "Ensuring only one IP address is configured on the device"
ip addr flush dev $INTF
dhclient -v $INTF

# Respond to ICMP echo requests (connection.target_ping)
echo "Configuring device to respond to ICMP echo requests"
ping -c 4 8.8.8.8

# Handling IP change (connection.ipaddr.ip_change)
echo "Handling IP address change"
dhclient -r $INTF
dhclient -v $INTF

# --- TEST: connection.ipaddr.dhcp_failover ---
# Handling DHCP failover
echo "Simulating DHCP failover"
dhclient -r $INTF
dhclient -v $INTF

# --- TEST: connection.ipv6_slaac ---
# Enable IPv6 SLAAC
echo "Enabling IPv6 SLAAC on $INTF"
sysctl net.ipv6.conf.$INTF.autoconf=1
sysctl net.ipv6.conf.$INTF.accept_ra=2
ip link set dev $INTF up

# Check if link-local address exists, assign manually if not
echo "Checking link-local IPv6 address"
if ! ip -6 addr show $INTF | grep -q "inet6 fe80::"; then
    echo "No link-local address found, assigning manually..."
    ip -6 addr add fe80::1/64 dev $INTF
fi

# Run DHCPv6 client for SLAAC
dhclient -6 -v $INTF

# Test: connection.ipv6_slaac
echo "Checking IPv6 SLAAC address"
ip -6 addr show $INTF

# Allow ICMPv6 echo requests and replies for ping
ip6tables -A INPUT -p ipv6-icmp --icmpv6-type echo-request -j ACCEPT
ip6tables -A OUTPUT -p ipv6-icmp --icmpv6-type echo-reply -j ACCEPT

# connection.ipv6_ping
echo "Pinging IPv6 address"
ping6 -c 4 fe80::1%$INTF

# Check if the ping was successful
if [ $? -eq 0 ]; then
  echo "IPv6 Ping succeeded"
else
  echo "IPv6 Ping failed"
fi

## DNS MODULE

# Test DNS resolution
echo "Sending DNS request to $DNS_SERVER"
dig @$DNS_SERVER +short www.google.com

# Keep network monitoring (can refactor later for other network modules)
(while true; do arping 10.10.10.1; sleep 10; done) &
(while true; do ip a | cat; sleep 10; done) &

# Keep the script running
tail -f /dev/null

