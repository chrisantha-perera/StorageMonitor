#Minimal Ubuntu 22:04 image

FROM ubuntu:22.04

# Install Python
RUN apt-get update && apt-get install -y python3 python3-pip

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip3 install -r /app/requirements.txt

