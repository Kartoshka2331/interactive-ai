#!/bin/bash

if [ -n "$SSH_ROOT_PASSWORD" ]; then
    echo "root:$SSH_ROOT_PASSWORD" | chpasswd
fi

/usr/sbin/sshd -D