import sys
import time
import subprocess
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import asyncio
import websockets

MAIN_SCRIPT = "server.py"
process = None
clients = set()

# 🔹 WebSocket Server (للتحديث التلقائي في المتصفح)
async def notify_clients():
    if clients:
        await asyncio.wait([client.send("reload") for client in clients])

async def ws_handler(websocket, path):
    clients.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        clients.remove(websocket)

def start_ws_server():
    asyncio.run(websockets.serve(ws_handler, "localhost", 8765))
    asyncio.get_event_loop().run_forever()

# 🔹 File Watcher
class AutoReloader(FileSystemEventHandler):
    def on_modified(self, event):
        global process
        
        print(f"🔁 File changed: {event.src_path}")
        print("Restarting server and notifying browser...")
        if process:
            process.kill()
        process = subprocess.Popen([sys.executable, MAIN_SCRIPT])
        asyncio.run(notify_clients())

if __name__ == "__main__":
    # Start WebSocket server in a background thread
    threading.Thread(target=start_ws_server, daemon=True).start()

    # Run file watcher
    event_handler = AutoReloader()
    observer = Observer()
    observer.schedule(event_handler, ".", recursive=True)
    observer.start()

    process = subprocess.Popen([sys.executable, MAIN_SCRIPT])

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        if process:
            process.kill()
    observer.join()
