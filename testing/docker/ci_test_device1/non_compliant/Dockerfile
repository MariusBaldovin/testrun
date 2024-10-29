FROM ubuntu@sha256:sha256:77d57fd89366f7d16615794a5b53e124d742404e20f035c22032233f1826bd6a


ENV DEBIAN_FRONTEND=noninteractive

# Update the package list and upgrade the installed packages to their latest versions
RUN apt-get update && apt-get -y upgrade

# Install the necessary packages
RUN apt-get update && apt-get install -y \
    isc-dhcp-client \
    dnsutils \
    netcat-openbsd \
    arping \
    ntp \
    ntpdate \
    iputils-ping \
    procps \
    iproute2 \
    xfce4 \
    xfce4-goodies \
    tightvncserver \
    dbus-x11 \
    xfonts-base \
    net-tools \
    telnet 

# Clean up the package lists to reduce the image size
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Setup VNC server
RUN mkdir /root/.vnc \
    && echo "password" | vncpasswd -f > /root/.vnc/passwd \
    && chmod 600 /root/.vnc/passwd \
    && touch /root/.Xauthority

COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

EXPOSE 5901
EXPOSE 6001