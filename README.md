#Controllbox

Naughty nerds playing with a Pi.

Installation:
- Put the files and folders from LINUX_ROOT into the linux root directory "/" (not "/root/") of Raspbian/Raspberry Pi OS
- Install the dependencies:
	sudo apt install python3-dev python3-rpi.gpio python3-opencv python3-flask python3-picamera python3-smbus
- reload, enable and start the service:
	systemctl daemon-reload; systemctl enable controllbox; systemctl start controllbox
- write protect the filesystem by enabling the Overlay-FS:
	raspi-config -> Advanced -> Overlay-FS



