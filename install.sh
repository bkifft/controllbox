#!/bin/bash
sudo apt update
sudo apt dist-upgrade -y
sudo apt autoremove -y
sudo apt install python3-dev python3-flask python3-smbus python3-picamera python3-schedule
sudo ln -sf "`pwd`/LINUX_ROOT/opt/controllbox/" /opt/controllbox/
sudo ln -sf "`pwd`/LINUX_ROOT/etc/systemd/system/controllbox.service" /etc/systemd/system/controllbox.service
sudo systemctl daemon-reload
sudo systemctl enable controllbox
sudo systemctl start controllbox



