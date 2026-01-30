FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    vim \
    nano \
    unzip \
    zip \
    tar \
    tree \
    jq \
    htop \
    software-properties-common \
    build-essential \
    make \
    cmake \
    g++ \
    gcc \
    openssh-server \
    nmap \
    net-tools \
    iputils-ping \
    dnsutils \
    sshpass \
    python3 \
    python3-pip \
    python3-venv \
    python3-full \
    openjdk-17-jdk \
    nodejs \
    npm \
    ffmpeg \
    imagemagick \
    && rm -rf /var/lib/apt/lists/*

RUN rm /usr/lib/python3.*/EXTERNALLY-MANAGED

RUN pip3 install --no-cache-dir \
    requests \
    pandas \
    numpy \
    beautifulsoup4 \
    lxml \
    httpx \
    yarl \
    psutil \
    scipy \
    matplotlib

RUN mkdir /var/run/sshd
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

RUN echo 'root:securepassword123' | chpasswd

WORKDIR /root
RUN mkdir -p /root/data

EXPOSE 22

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]