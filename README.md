# API for Pimoroni Blinkt! hat
http://docs.pimoroni.com/blinkt/
https://shop.pimoroni.com/products/blinkt

## Install

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
