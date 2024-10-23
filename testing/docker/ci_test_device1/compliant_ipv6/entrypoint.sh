#!/bin/bash -x

# Display network interfaces
ip a

# Set paths and servers
NTP_SERVER=10.10.10.5
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

# Setup IPv6 SLAAC configuration
echo "Setting up IPv6 SLAAC"
sysctl net.ipv6.conf.$INTF.autoconf=1
sysctl net.ipv6.conf.$INTF.accept_ra=1
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

# Test: connection.ipv6_ping
echo "Pinging IPv6 address"
ping6 -c 4 fe80::1%$INTF

# Keep the script running to allow further interactions
tail -f /dev/null
