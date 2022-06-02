# UniTree Go1 Setup Guide
Setup guide for the UniTree Go1 robot. Here: https://www.yuque.com/ironfatty/ibngax/sc8u0h

## Config Your SSH

The password is `123` the username is `unitree`.

```in
Host go1-pi
    Hostname 192.168.123.161
    User pi
Host go1-nano2gb
    Hostname 192.168.123.13
    User unitree
Host go1-unitree-desktop
    Hostname 192.168.123.14
    User unitree
Host go1-nx
    Hostname 192.168.123.15
    User unitree
```



## Configuring Wifi on Rasberry Pi

More information on pi: https://www.raspberrypi.com/documentation/computers/configuration.html#setting-up-a-routed-wireless-access-point
```bash
ifconfig
vim /etc/network/interfaces
sud vim /etc/network/interfaces
sudo iwlist wlan1 scan
sudo reboot -h now
vim /etc/wpa_supplicant/wpa_supplicant.conf
sud vim /etc/wpa_supplicant/wpa_supplicant.conf
sudo reboot -h now
ifconfig
sudo ifconfig wlan0 up
ifconfig
sudo ifconfig wlan2 up
ping 8.8.8.8
vim /etc/wpa_supplicant/wpa_supplicant.conf
ifconfig
ping 192.168.39.1
ip route show
ping baidu.com
sudo route add default gw 128.31.32.1
ping baidu. com
sudo apt update
sudo apt install snapd
history
sudo reboot -h now
sudo snap install core
ifconfig
sudo ifconfig wlan® up
ip route show
sudo ifconfig wlan1 up
sudo ifconfig wlan2 up
ifconfig
ip route show
sudo route add default gw 128.31.32.1
ping baidu.com
sudo snap install core
sudo snap install ngrok
history
pip
pip install proxy.py
python
pip3 install proxy.py
python?
-m proxy.py
python?
-m proxy
python3
-m proxy
-p 3128
python?
-m proxy
-port 3128
history
```



## Install `ngrok` and `proxy.py` on Pi

```bash
sudo apt update
sudo apt install snapd
```

You will also need to reboot your device:

```bash
sudo reboot
```

After this, install the core snap in order to get the latest snapd:

```bash
sudo snap install core
sudo snap install ngrok
```

Now install `proxy.py`

```bash
pip3 install proxy.py
```



now on other matchines:

```bash
unitree@unitree-desktop:~$ 
sudo snap set system proxy.http="http://192.168.123.161:3128"
sudo snap set system proxy.https="http://192.168.123.161:3128"
sudo snap install core ngrok
```





## Using http_proxy for apt install

From: https://askubuntu.com/a/19298

**Note:** Using `visudo` is fairly dangerous and can break things. Make sure you only save when the file is correct.

In some releases sudo is configured in such a way that all environment variables all cleared when running the command. To keep the value for your **http_proxy** and fix this, you need to edit /etc/sudoers, run:

```
visudo
```

Then find a line that states:

```
Defaults env_reset 
```

and add after it:

```
Defaults env_keep="http_proxy ftp_proxy" 
```

Things will start working as expected.

Thanks to **kdogksu** in the Ubuntu Forums for finding the [solution](http://ubuntuforums.org/showpost.php?p=9845413&postcount=5) for this.

In order to not only fix apt-get but also graphical X11 utils as e.g synaptic,mintintall, ...) the following line in `/etc/sudoers` should do the job :

```
Defaults env_keep = "http_proxy https_proxy ftp_proxy DISPLAY XAUTHORITY"
```

