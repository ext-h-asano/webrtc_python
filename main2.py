import asyncio
import websockets
import ssl
import json
import numpy as np
import cv2
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate, VideoStreamTrack
from av import VideoFrame
import subprocess

SSL_PORT = 8443
SERVER_ADDRESS = 'wss://52.194.235.65:' + str(SSL_PORT)

#SSL検証を無効にする
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


local_id = 'aaapython'
remote_id = 'bbbpython'
pc = None
sc = None

def execute_adb_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"ADB command executed: {command}")
    except subprocess.CalledProcessError as e:
        print(f"Error executing ADB command: {e}")

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


class VirtualDeviceVideoStreamTrack(VideoStreamTrack):
    def __init__(self):
        super().__init__()
        self.cap = cv2.VideoCapture('/dev/video0')  # 仮想デバイスのパスを指定

    async def recv(self):
        ret, frame = self.cap.read()
        if not ret:
            return None

        # OpenCVのBGR形式からRGB形式に変換
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = VideoFrame.from_ndarray(frame, format="rgb24")
        frame.pts, frame.time_base = await self.next_timestamp()

        return frame

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
    global pc
    signal = json.loads(message)

    if signal.get("start"):
        await start_peer_connection(signal["start"])
        print("startを受けたからピア接続を開始")
        return
    
    if signal.get("close"):
        await stop_peer_connection()
        print("ピア接続を閉じました")
        return
    
    if signal.get("ping"):
        await sc.send(json.dumps({"pong": 1}))
        return
    
    if not pc:
        return
    
    #以下でシグナリング処理を行う。
    if signal.get("sdp"):
        sdp = signal["sdp"]
        if sdp["type"] == "offer":
            await pc.setRemoteDescription(RTCSessionDescription(sdp["sdp"], sdp["type"]))
            answer = await pc.createAnswer()
            await set_description(answer)
        elif sdp["type"] == "answer":
            await pc.setRemoteDescription(RTCSessionDescription(sdp["sdp"], sdp["type"]))

    if signal.get("ice"):
        ice = signal["ice"]
        ice_candidate = RTCIceCandidate(
            component=1,  # Assuming this is always 1 for RTP
            foundation=ice["candidate"].split()[0].split(':')[1],
            ip=ice["candidate"].split()[4],
            port=int(ice["candidate"].split()[5]),
            priority=int(ice["candidate"].split()[3]),
            protocol=ice["candidate"].split()[2],
            type=ice["candidate"].split()[7],
            sdpMid=ice["sdpMid"],
            sdpMLineIndex=ice["sdpMLineIndex"]
        )
        await pc.addIceCandidate(ice_candidate)
        print(f"ICE candidate added: {ice['candidate']}")


async def start_peer_connection(sdp_type):
    global pc
    pc = RTCPeerConnection()

    @pc.on("icecandidate")
    async def on_icecandidate(candidate):
        if candidate:
            print("iceを送りました。")
            await sc.send(json.dumps({"ice": {
                "candidate": candidate.sdp,
                "sdpMLineIndex": candidate.sdpMLineIndex,
                "sdpMid": candidate.sdpMid
            }, "remote": remote_id}))

    @pc.on("track")
    def on_track(track):
        if track.kind == "video":
            print("Receiving video track")
        elif track.kind == "audio":
            print("Receiving audio track")


    # 接続状態の監視を追加
    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print(f"Connection state is {pc.connectionState}")
        if pc.connectionState == "failed":
            print("Connection failed. Closing peer connection.")
            await stop_peer_connection()

    # 仮想デバイスのビデオトラックを追加
    video_track = VirtualDeviceVideoStreamTrack()
    pc.addTrack(video_track)

    # Offer/Answerの作成
    if sdp_type == "offer":
        offer = await pc.createOffer()
        await set_description(offer)

    @pc.on("datachannel")
    def on_datachannel(channel):
        print(f"kaisetu{channel.label}")

        @channel.on("message")
        def on_message(message):
            print(message)
            try:
                data = json.loads(message)
                if data['type'] == "touch":
                    handle_touch_event(data)
                elif data['type'] == "swipe":
                    handle_swipe_event(data)
                else:
                    print("miti")
            except:
                print("shippai")

async def set_description(description):
    global pc
    await pc.setLocalDescription(description)
    await sc.send(json.dumps({"sdp": {
        "type": description.type,
        "sdp": description.sdp
    }, "remote": remote_id}))


async def stop_peer_connection():
    global pc
    if pc:
        await pc.close()
        pc = None

async def main():
    await start_server_connection()

asyncio.run(main())
