# btlock Dev Journal

## 11092024

Step 1, get Micropython working on this board.

```
pip install esptool
esptool.py --port /dev/ttyUSB0 erase_flash
esptool.py --chip esp32 --port /dev/ttyUSB0 --baud 460800 write_flash -z 0x1000 ESP32_GENERIC-20241025-v1.24.0.bin
```

Now let's see if we can talk to it:
```
picocom -b 115200 /dev/ttyUSB0
```

Cool!  Let's see if it can see the wifi networks:
```
>>> import network
>>> sta_if = network.WLAN(network.STA_IF)
>>> ap_if = network.WLAN(network.AP_IF)
>>> ap_if.active()
False
>>> sta_if.active()
False
>>> sta_if.active(True)
True
>>> sta_if.connect('wifican', 'dementia13')
>>> sta_if.isconnected()
True
>>> sta_if.ipconfig('addr4')
('192.168.68.74', '255.255.252.0')
>>> 
```

OK, now let's see if we can figure the bluetooth stuff out.

First, install `aioble`:
```
>>> import mip
>>> mip.install("aioble")
Installing aioble (latest) from https://micropython.org/pi/v2 to /lib
Copying: /lib/aioble/__init__.mpy
Copying: /lib/aioble/core.mpy
Copying: /lib/aioble/device.mpy
Copying: /lib/aioble/peripheral.mpy
Copying: /lib/aioble/server.mpy
Copying: /lib/aioble/central.mpy
Copying: /lib/aioble/client.mpy
Copying: /lib/aioble/l2cap.mpy
Copying: /lib/aioble/security.mpy
Done
```

hmm... hard to write async code in the REPL...

```
>>> import asyncio
>>> import aioble
>>> import bluetooth
>>> loop = asyncio.get_event_loop()
>>> async def demo():
...     async with aioble.scan(duration_ms=5000) as scanner:
...         async for result in scanner:
...             print(result, result.name(), result.rssi, result.services())
...             
...             
... 
>>> loop.run_until_complete(demo())
Scan result: Device(ADDR_PUBLIC, e7:a1:09:20:40:c6) -79 None -79 <generator object 'services' at 3ffdd2f0>
Scan result: Device(ADDR_PUBLIC, f7:57:77:e1:45:94) -91 None -91 <generator object 'services' at 3ffdd620>
Scan result: Device(ADDR_PUBLIC, e7:a1:09:20:40:c6) -83 None -83 <generator object 'services' at 3ffd0050>
Scan result: Device(ADDR_PUBLIC, f7:57:77:e1:45:94) -81 None -81 <generator object 'services' at 3ffd0410>
Scan result: Device(ADDR_PUBLIC, f7:57:77:e1:45:94) -82 None -82 <generator object 'services' at 3ffd0d40>
Scan result: Device(ADDR_PUBLIC, e7:a1:09:20:40:c6) -84 None -84 <generator object 'services' at 3ffd1060>
Scan result: Device(ADDR_RANDOM, 78:f5:45:6d:0e:fc) -75 None -75 <generator object 'services' at 3ffd13b0>
...
```

That worked!

Now let's try and talk to one of them:
```
>>> device = aioble.Device(aioble.ADDR_PUBLIC, "f7:57:77:e1:45:94")
>>> async def connectit(d):
...     try:
...         print("Connecting to", d)
...         connection = await device.connect()
...     except asyncio.TimeoutError:
...         print("timeout")
...         return
...         
...         
... 
>>> asyncio.run(connectit(device))
Connecting to Device(ADDR_PUBLIC, f7:57:77:e1:45:94)
>>> device
<Device object at 3ffd2530>
>>> print(device)
Device(ADDR_PUBLIC, f7:57:77:e1:45:94, CONNECTED)
```

After doing this, I can no longer connect to one of my Bluetti devices using the mobile app!  Let's see if we can "unlock" it:
```
>>> async def unlock(d):
...     print("unlocking", d)
...     await d._connection.disconnect(timeout_ms=2000)
...     
...     
... 
>>> asyncio.run(unlock(device))
unlocking Device(ADDR_PUBLIC, f7:57:77:e1:45:94, CONNECTED)
```

That unlocked it!

So I think there's enough scraps here to perform basic locking/unlocking of a ble device.  Clearly there's lots to do wrt figuring out how to select devices by name (instead of guessing by MAC or whatever) and wrapping it in some sort of interface, but as a PoC, it's not bad!



### References
* https://heltec.org/project/wifi-kit32-v3/
* https://micropython.org/download/ESP32_GENERIC/
* https://github.com/micropython/micropython-lib/tree/master/micropython/bluetooth/aioble
* https://docs.micropython.org/en/latest/reference/packages.html
* https://docs.micropython.org/en/latest/esp8266/tutorial/filesystem.html
