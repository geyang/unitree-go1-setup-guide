# UniTree Go1 Setup Guide
Setup guide for the UniTree Go1 robot. Here: https://www.yuque.com/ironfatty/ibngax/sc8u0h

## Connecting to Go1

Need to configure your connection to join the intranet.

```bash
❯ sudo ifconfig en7 down
Password:
❯ sudo ifconfig en7 192.168.123.162/24
❯ sudo ifconfig en7 up
```

## Config Your SSH

The password is `123` the username is `unitree`.

```in
# inside your ~/.ssh/config
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

## Updating the onboard clock

All three computer's internal clocks are off. Wrong system date causes the `apt install` to report invalid dates (it compares the system date with a cutoff). If you run

```bash
unitree@nx:~ $ date
Sun 05 Jun 2022 05:28:03 PM EDT
```

Here I recommend this super legitimate 🤞, unsanitized script from [[The Internet]](https://superuser.com/questions/307158/how-to-use-ntpdate-behind-a-proxy) under sudo:

```bash
sudo date -s "$(wget -S  "http://www.google.com/" 2>&1 | grep -E '^[[:space:]]*[dD]ate:' | sed 's/^[[:space:]]*[dD]ate:[[:space:]]*//' | head -1l | awk '{print $1, $3, $2,  $5 ,"GMT", $4 }' | sed 's/,//')"
```



## Connecting Rasberry Pi to WiFi

Three things need to happen

1. **Setting up with `wpa_cli`**: 

   ```bash
   wpa_cli -i wlan0
   > status
   > ADD_NETWORK
   3
   > SET_NETWORK 3 ssid "<your-ssid>"
   > SET_NETWORK 3 psk "<your-password>" // etc
   > SELECT_NETWORK 3
   > status
   > SCAN_RESULTS
   ```

   The status should show that the network is still `INACTIVE`, this is because WiFi has not been turned on yet. We will turn it on next.

2. **Now turn on wifi**

   ```bash
   sudo ifconfig wlan0 up
   ```

   When the WiFi turns on, the status should instantly change to show 

3. **Adding the correct gateway to route** This one is a bit tricky (and unreliable)

   First, you can check the routing configurations already setup in pi:

   ```bash
   > route -n
   Kernel IP routing table
   Destination     Gateway         Genmask         Flags Metric Ref    Use Iface
   0.0.0.0         192.168.123.1   0.0.0.0         UG    202    0        0 eth0
   0.0.0.0         128.31.32.1     0.0.0.0         UG    303    0        0 wlan0
   0.0.0.0         192.168.12.1    0.0.0.0         UG    305    0        0 wlan1
   128.31.32.0     0.0.0.0         255.255.248.0   U     303    0        0 wlan0
   192.168.12.0    0.0.0.0         255.255.255.0   U     305    0        0 wlan1
   192.168.123.0   0.0.0.0         255.255.255.0   U     202    0        0 eth0
   224.0.0.0       0.0.0.0         240.0.0.0       U     0      0        0 lo
   ```

   In this case the wireless gateway is placed after the ethernet, which does not have the www access. We can move it forward by first removing it, and then adding it back again.

   If you are setting this up for the first time, you would not have this wlan0 gateway. You can skip the removing step in this case.

   ```bash
   sudo route remove default gw <your-gateway-ip>
   sudo route add default gw <your-gateway-ip>
   ```

   Before doing this, you should be able to ping that gate-way IP address. 

   

4. **Changing the priority on the default gateway** from `eth0` to `wlan0`

   The problem I still run into, is that sometimes the routing order gets changed back. With the help of [[this thread: Change priority on the default gateway]](https://forums.raspberrypi.com/viewtopic.php?t=278033) in the raspberry pi forum, we are able to fix this issue.

   

   Edit the file `/etc/dhcpcd.conf` and append the following to the file

   ```bash
   interface wlan0
   metric 100
   ```

   ```bash
   > route -n
   Kernel IP routing table
   Destination     Gateway         Genmask         Flags Metric Ref    Use Iface
   0.0.0.0         128.31.32.1     0.0.0.0         UG    0      0        0 wlan0
   0.0.0.0         192.168.123.1   0.0.0.0         UG    202    0        0 eth0
   0.0.0.0         192.168.12.1    0.0.0.0         UG    305    0        0 wlan1
   128.31.32.0     0.0.0.0         255.255.248.0   U     303    0        0 wlan0
   192.168.12.0    0.0.0.0         255.255.255.0   U     305    0        0 wlan1
   192.168.123.0   0.0.0.0         255.255.255.0   U     202    0        0 eth0
   224.0.0.0       0.0.0.0         240.0.0.0       U     0      0        0 lo
   ```

   

   

## Setting up internet access for Nano and NX

I setup www access on the nano and the NX using a proxy server on the raspberry pi:

```bash
# On raspberrypi
screen -dm python3 -m proxy --host 0.0.0.0 --port 3128
```

Then on Nano and NX: we edit the `~/.profile` file because this is only needed when running from a login shell.

```bash
# Edit ~/.profile
export http_proxy=http://192.168.123.161:3128
export https_proxy=http://192.168.123.161:3128
export ftp_proxy=http://192.168.123.161:3128
```

In many releases sudo is configured such that all environment variables are cleared when running the command. To allow `apt` and `apt-get` to use these proxy settings, we need to use `visudo` to modify the sudoer file. **NOTE: Using `visudo` is fairly dangerous and can break your shell, so make sure the file is correct before saving and exiting it.**

```
visudo
```

Then find a line that states:

```
Defaults env_reset 
```

and add after it:

```
Defaults env_reset  # <= previous line
Defaults env_keep="http_proxy ftp_proxy" 
```

Things will start working as expected.

```bash
sudo apt install git tree 
```



## Setting up proxy for docker daemon

When trying to `docker pull` or `docker build` on the jetson, you might have ran into this error despite of having `http(s)_proxy` set to the pi.

```bash
Error response from daemon: Get https://registry-1.docker.io/v2/: dial tcp: lookup registry-1.docker.io on 127.0.0.53:53: read udp 127.0.0.1:46641->127.0.0.53:53: i/o timeout
```

This happens because the docker daemon is ran as a system process, so similar to `sudo apt install`, it does not respect the `http_proxy` flag that you set in the `unitree` user's shell session. For this reason, we need to set the proxy variables in the daemo systemd config file.

1. Create a new directory for our Docker service configurations.

   ```
   sudo mkdir -p /etc/systemd/system/docker.service.d
   ```

2. Create a file called proxy.conf in our configuration directory.

   ```
   sudo vi /etc/systemd/system/docker.service.d/proxy.conf
   ```

3. Add the following contents, changing the values to match your environment.

   ```
   [Service]
   Environment="HTTP_PROXY=http://myproxy.hostname:8080"
   Environment="HTTPS_PROXY=https://myproxy.hostname:8080/"
   Environment="NO_PROXY="localhost,127.0.0.1,::1"
   ```

4. Save your changes and exit the text editor.

5. Reload the daemon configuration.

   ```
   sudo systemctl daemon-reload
   ```

6. Restart Docker to apply our changes.

   ```
   sudo systemctl restart docker.service
   ```

After the service is restarted Docker should be able to pull images from external repositories. You can test this by attempting to pull down an image. If the download completes and does not timeout, your proxy settings have been applied.



## Deploying the Trained Controller

1. compile the Unitree legged sdk on nano. This one runs the lcm driver.
2. compile the docker image on nano using docker. This is the controller that communicates with the lcm driver.

### Step 1: Compiling the unitree legged sdk on nano





---





## Configuring Wifi on Rasberry Pi

More information on pi: https://www.raspberrypi.com/documentation/computers/configuration.html#setting-up-a-routed-wireless-access-point

Need to configure your connection to join the intranet.

```bash
❯ sudo ifconfig en7 down
Password:
❯ sudo ifconfig en7 192.168.123.162/24
❯ sudo ifconfig en7 up
```

test







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
ip route show
ping baidu.com
sudo route add default gw 128.31.32.1
ping baidu. com
sudo apt update
sudo apt install snapd
sudo reboot -h now
sudo snap install core
ifconfig
ip route show
sudo ifconfig wlan1 up
sudo ifconfig wlan2 up
ifconfig
ip route show
sudo route add default gw 128.31.32.1
ping baidu.com
sudo snap install core
sudo snap install ngrok
pip install proxy.py
pip3 install proxy.py
python3 -m proxy -p 3128
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

**Note:** Using `visudo` is fairly dangerous and can break things. Make sure you only save when the file is correct.

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
Defaults env_keep = "https_proxy ftp_proxy"
```





## Connect Rasberry PI to Internet

Look up the gateway on a computer in the same network.

```bash
  151  sudo route delete default gw 128.31.37.181
  152  sudo route add default gw 128.31.32.1
  153  ping 8.8.8.8
```



The `wlan0` is the wifi card that you should use.

```bash
wpa_cli -i wlan0
```



https://askubuntu.com/questions/62166/siocsifflags-operation-not-possible-due-to-rf-kill

```
$ sudo rfkill list all

0: phy0: Wireless LAN 

     Soft blocked: yes

     Hard blocked: no

1: tpacpi_bluetooth_sw: Bluetooth

     Soft blocked: yes

     Hard blocked: yes
```

## Next Steps

1. compile the docker image
2. compile the 





## Install Github CLI

```
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh
```





Compiling UnitreeCameraSDK:



```bash
sudo apt install libudev1 libudev-dev
gh clone UnitreeCameraSDK
cd UnitreeCameraSDK
mkdir build 
cd build
cmake ..
make
```

|      |      | [Go1 robot]                                                  |
| ---- | ---- | ------------------------------------------------------------ |
|      |      | NanoA: Jetson Nano (Go1's Head, IP: 192.168.123.13)          |
|      |      | NanoB: Jetson Nano (Go1's Body, IP: 192.168.123.14)          |
|      |      | NanoC: Jetson Nano (Go1's Body, IP: 192.168.123.15)          |
|      |      | (Raspi board has OpenCV 3.x by default. This SDK need OpenCV 4.x .) |
|      |      | You can login to console by SSH / GUI.                       |
|      |      |                                                              |
|      |      |                                                              |
|      |      | [example source]                                             |
|      |      | exPUT2: example_putimagetrans2.cc (This example. Sender)     |
|      |      | exPUT:  example_putimagetrans.cc  (Basic example. Sender)    |
|      |      | exGET:  example_getimagetrans.cc  (Receiver)                 |
|      |      |                                                              |
|      |      | Sender <---> Receiver                                        |

