# API for Pimoroni Blinkt! hat
http://docs.pimoroni.com/blinkt/
<br>
https://shop.pimoroni.com/products/blinkt

<br>

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
