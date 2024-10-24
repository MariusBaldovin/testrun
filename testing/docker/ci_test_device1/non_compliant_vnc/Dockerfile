FROM ubuntu@sha256:e6173d4dc55e76b87c4af8db8821b1feae4146dd47341e4d431118c7dd060a74

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

# Expose the VNC port (5901 for display :1)
EXPOSE 5901