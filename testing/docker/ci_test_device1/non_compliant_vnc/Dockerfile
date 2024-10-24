FROM ubuntu@sha256:77d57fd89366f7d16615794a5b53e124d742404e20f035c22032233f1826bd6a

ENV DEBIAN_FRONTEND=noninteractive

# Update the package list and upgrade the installed packages to their latest versions
RUN apt-get update && apt-get -y upgrade

# Install the necessary packages
RUN apt-get update && apt-get install -y tightvncserver xfce4

# Clean up the package lists to reduce the image size
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Set environment variables for VNC
ENV DISPLAY=:1

# Set up the VNC server password (could be dummy, as you won’t use it)
RUN mkdir ~/.vnc && echo "password" | vncpasswd -f > ~/.vnc/passwd && chmod 600 ~/.vnc/passwd

# Start the VNC server automatically when the container starts
CMD ["tightvncserver", ":1", "-geometry", "1280x800", "-depth", "24"]

# Expose the VNC port
EXPOSE 5901