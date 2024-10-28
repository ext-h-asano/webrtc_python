import asyncio
import websockets
import ssl
import json
import subprocess
import time

SSL_PORT = 3001
SERVER_ADDRESS = 'wss://handling.android-vpn.com:' + str(SSL_PORT)

#SSL検証を無効にする
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


local_id = 'aaapython'
remote_id = 'bbbpython'
sc = None

def execute_adb_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"ADB command executed: {command}")
    except subprocess.CalledProcessError as e:
        print(f"Error executing ADB command: {e}")

def execute_init_commands(data):
    subprocess.run("./launch-waydroid.sh")

def execute_restart_commands(data):
    subprocess.run("./scrcpy-waydroid.sh")


def execute_waydroid_commands(data):
    width = data['width']
    height = data['height']
    commands = [
        "adb disconnect",
        "adb connect 192.168.240.112:5555",
        f"adb shell wm size {width}x{height}",
        "waydroid session stop",
    ]

    for command in commands:
        try:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            print(f"コマンドの実行success: {command}")
            print(f"出力:{result.stdout}")
            time.sleep(1)
        except subprocess.CalledProcessError as e:
            print(f"コマンドの実行失敗: {e}")
            return False
    return True


def handle_touch_event(data):
    if 'x' not in data or 'y' not in data:
        print("Invalid touch event data")
        return

    x = data['x']
    y = data['y']
    
    abs_x = int(x)
    abs_y = int(y)
    
    adb_command = f"adb shell input tap {abs_x} {abs_y}"
    execute_adb_command(adb_command)

def handle_swipe_event(data):
    if 'startX' not in data or 'startY' not in data or 'endX' not in data or 'endY' not in data:
        print("Invalid swipe event data")
        return

    start_x = data['startX']
    start_y = data['startY']
    end_x = data['endX']
    end_y = data['endY']
    
    abs_start_x = int(start_x)
    abs_start_y = int(start_y)
    abs_end_x = int(end_x)
    abs_end_y = int(end_y)
    
    duration = 300
    
    adb_command = f"adb shell input swipe {abs_start_x} {abs_start_y} {abs_end_x} {abs_end_y} {duration}"
    execute_adb_command(adb_command)


async def start_server_connection():
    print('開始')
    #websocketにIDを送信して、接続を試みる
    global sc
    sc = await websockets.connect(SERVER_ADDRESS, ssl=ssl_context)
    await sc.send(json.dumps({"open": {"local": local_id, "remote": remote_id}}))
    print('終了')
    while True:
        message = await sc.recv()
        await got_message_from_server(message)


async def got_message_from_server(message):
    signal = json.loads(message)
    print(f'{signal} : testetetertertrtert')

    if 'type' in signal:
        if signal['type'] == "touch":
            handle_touch_event(signal)
        elif signal['type'] == "swipe":
            handle_swipe_event(signal)
        elif signal['type'] == "screen_size":
            execute_waydroid_commands(signal)
        elif signal['type'] == "init":
            execute_init_commands(signal)
        elif signal['type'] == "restart":
            execute_restart_commands
        else:
            print("Unknown type")
    else:
        print("Key 'type' not found in signal")



async def main():
    await start_server_connection()

asyncio.run(main())

