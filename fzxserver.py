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
