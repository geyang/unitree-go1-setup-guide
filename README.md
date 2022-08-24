# UniTree Go1 Setup Guide
Setup guide for the UniTree Go1 robot. Here: https://www.yuque.com/ironfatty/ibngax/sc8u0h



All of the guides are available here [[guide]](guide).

- [[Setting up Networking]](setting_up_networking.md): this guide gives you full interenet access and wifi conectivity on the robot
- [[Deployment]](deployment.md): this guides shows you how to deploy the trained neural controller on the robot
- [[Training in Isaac Gym]]: this guide shows you how to train a control policy
- [[Working with LCM and Coms]]: this guide shows you how to add or modify the LCM interface for more controls.



## Connecting to Go1

**A full version of this is available in the [[Setting up Networking guide]](setting_up_networking.md)**. 

First, you need to configure your connection to join the intranet.

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