# btlock Dev Journal

## 11102024

Let's try turning this into a proper program now.

I think a physical interface makes sense, but I don't have any additional hardware handy, so instead I think we'll do a little web interface for now and add hardware later.

I've got a nice workflow using `rshell`:
```
$ rshell
/home/jason/Development/btlock> connect serial /dev/ttyUSB0
/home/jason/Development/btlock> edit /pyboard/fzxserver.sh
/home/jason/Development/btlock> repl
>>> import fzxserver
```

This creates the file `fzxserver.sh` in the board's flash, edits it using my default editor (micro) and runs it via the REPL.  CTRL-D resets the REPL (needed between runs of the program) and CTRL-X exits the REPL.

Since I'm working the file directly on the board, I have to copy it back to my laptop's filesystem to update the repo:
```
/home/jason/Development/btlock> cp /pyboard/fzxserver.py ./
```

I got a very basic web server working using `asyncio`:
``` python
import socket
import time
import asyncio

html = """<!DOCTYPE html>
<html>
  <head>
    <title>bluelocker</title>
  </head>
  <body>
    <h1>Bluelocker</h1>
  </body>
</html>
"""

async def serve(reader, writer):
  print("client connected")
  request_line = await reader.readline()
  print("Request:", request_line)
  # ignore headers for now
  while await reader.readline() != b"\r\n":
    pass

  # TODO: dump all request details to the log for examination

  response = html
  writer.write("HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n")
  writer.write(response)

  await writer.drain()
  await writer.wait_closed()
  print("client disconnected")

async def main():
  print("starting server")
  asyncio.create_task(asyncio.start_server(serve, "0.0.0.0", 80))

  # maybe we need this infinate loop to keep things going?
  while True:
    print("heartbeat")
    #await asyncio.sleep(0.25)
    await asyncio.sleep(5)
    
try:
  asyncio.run(main())
finally:
  asyncio.new_event_loop()
```

...now to use this to control the bluetooth connection...


I'd like to make this a proper REST API, which means interpretting the HTTP verbs correctly.  `GET` is easy, but `POST` is a little more complicated.

To read the `POST` body we need to know the length, so we need to parse the headers.  Here's what they look like line-by-line:

```
Request: b'POST /lock1 HTTP/1.1\r\n'
Header: b'Host: 192.168.68.74\r\n'
Header: b'User-Agent: curl/7.81.0\r\n'
Header: b'Accept: */*\r\n'
Header: b'Content-Length: 16\r\n'
Header: b'Content-Type: application/x-www-form-urlencoded\r\n'
```




### References
* https://docs.micropython.org/en/latest/library/asyncio.html

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

Hours later I remembered [rshell](https://github.com/dhylands/rshell), that's going to make this easier...

> Note: the flash on this board can be found under `/pyboard` not `/flash`


### References
* https://heltec.org/project/wifi-kit32-v3/
* https://micropython.org/download/ESP32_GENERIC/
* https://github.com/micropython/micropython-lib/tree/master/micropython/bluetooth/aioble
* https://docs.micropython.org/en/latest/reference/packages.html
* https://docs.micropython.org/en/latest/esp8266/tutorial/filesystem.html
* https://github.com/dhylands/rshell
