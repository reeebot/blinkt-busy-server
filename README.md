# Web App & API for Pimoroni Blinkt! hat
<br>
NEW VERSION:  <a href="https://github.com/reeebot/myStatus">myStatus</a>

<br>
<br>
<img src="https://i.imgur.com/4mNwUn5.png">

## Install
...

<br>

## Service

```
sudo cp busylight.service /etc/systemd/system/busylight.service
```

Testing the service:

```
sudo systemctl start busylight.service
sudo systemctl stop busylight.service
sudo systemctl status busylight.service
```

Enable/disable for startup:

```
sudo systemctl enable busylight.service
sudo systemctl disable busylight.service
```
