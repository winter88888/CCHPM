import threading
import time
from queue import Queue
import socket
import json


class NetworkThread(threading.Thread):
    def __init__(self, host, port):
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self.running = False
        self.socket_connected = False
        self.send_queue = Queue()
        self.retry_interval = 5  # 重试间隔(秒)
        self.handshake_completed = False
        self.socket=None
        self.recv_buffer=b''

    def logErrorMessage(self,message:str,type:str):

        if hasattr(self, 'logHandler'):
            self.logHandler(message,type)


    def run(self):
        self.running = True
        while self.running:
            try:
                # 创建新连接
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.host, self.port))
                self.socket.setblocking(False)
                self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self.handshake_completed = False
                # 设置消息回调
                self.logErrorMessage("Connected to server successfully.","info")
                self.socket_connected = True
                # 主处理循环
                while self.socket_connected:
                    # 处理接收
                    self.handle_ready_read()
                    if not self.handshake_completed:
                        time.sleep(0.1)
                        continue

                    # 处理发送队列
                    while not self.send_queue.empty():
                        data = self.send_queue.get()
                        try:
                            self.send_threat_update(**data)
                        except Exception as e:
                            self.logErrorMessage(f"Sending failed: {str(e)}","info")

                    time.sleep(0.1)  # 降低CPU占用

            except ConnectionRefusedError:
                self.logErrorMessage(f"Connecting failed,retrying in {self.retry_interval}s...","info")
                time.sleep(self.retry_interval)
            except Exception as e:
                self.logErrorMessage(f"Connecting error: {str(e)}","info")
                time.sleep(self.retry_interval)

    def stop(self):
        self.running = False
        if self.socket:
            self.socket.close()

    def send_data(self, type:str,character_name, mob_name, threat_value):
        self.send_queue.put({
            "type": type,
            "character_name": character_name,
            "mobName": mob_name,
            "threat_value": threat_value,
        })


    def handle_ready_read(self):
        buffer=bytes()
        try:
            while True:  # 循环读取所有可用数据
                data = self.socket.recv(4096)
                if not data:
                    self.logErrorMessage("Connection closed by server.", "info")
                    self.socket.close()
                    self.socket = None
                    self.socket_connected = False
                    return  # 退出当前处理，让内部循环结束
                buffer+=data

        except BlockingIOError:    # 无数据可读时抛出此exception
            if not buffer:         # 未收到任何数据
                return
            self._process_received_data(buffer)   #handle the data recieved from server
        except Exception as e:
            self.logErrorMessage(f"Read error: {str(e)}", "info")
            if self.socket:
                self.socket.close()
                self.socket = None
            self.socket_connected = False

    def _process_received_data(self, data):

        if not self.handshake_completed:
            if data.startswith(b"SERVER:HANDSHAKE_CONFIRMED"):
                self.logErrorMessage("Handshake confirmation received from server.", "info")
                self.handshake_completed = True
                return

            if data.startswith(b"SERVER:HANDSHAKE"):
                self.logErrorMessage("Handshake message received from server.", "info")
                self.socket.send(b"CLIENT:HANDSHAKE")
                return
            self.logErrorMessage(f"Unexpected message during handshake phase. msg: {data}", "info")
            return  # return after handshake is completed.

        self.recv_buffer+=data     #handle frame fragment from last reception

        frames=self.extractFramesFromBuffer()

        for frame in frames:
            self._emit_message_received(frame)

    def extractFramesFromBuffer(self):

        #frame example:
        #{"mob_name":"A dire wolf","threat_list":[{"character":"Jumo","threat":76},{"character":"Kingdombot","threat":10000}],"type":"threat_broadcast"}
        #here we need do a integral check first , split the frames if there's any complete frame.
        #then maintain the recv_bufer, pop the data that's been handled. Leave the rest as fragemnt for succeed data.

        frames = []
        while True:
            # find the start of frame
            start_idx = self.recv_buffer.find(b'{"mob_name"')
            if start_idx == -1:
                break  # break if can't find more.

            # find the end of frame ( from last start position)
            end_marker = b'"type":"threat_broadcast"}'
            end_idx = self.recv_buffer.find(end_marker, start_idx)
            if end_idx == -1:
                break  # can't find any end mark , keep the remaining data in recieve buffer.

            # count the end position
            end_pos = end_idx + len(end_marker)
            # extract valid frames
            frame = self.recv_buffer[start_idx:end_pos]
            frames.append(frame)

            # update receive buffer , remove the handled data
            self.recv_buffer = self.recv_buffer[end_pos:]

        return frames


    def send_threat_update(self, type:str, character_name:str, mobName:str, threat_value:int):
        # 检查连接状态（需要根据实际网络库实现状态维护）
        if not self.handshake_completed:
            self.logErrorMessage("Not connected to server yet when trying to send aggro table.","info")
            return

        '''
        type:clear_all_aggro this will be indicating that the player has clear his aggro to all mobs he has been on. 
             So server side can safely remove this player from everymobs' agro list.
        type:mob_slain  this will be indicating that the mob has been slain by someone. 
             So the server side can safely remove the mob entry and his aggro table totally.
        type:threat_update this will be indicating that an aggro table for a mob from the player will be sent to the server.
             So need server to summarize the aggro table from all players then broad cast to all client.
              
                # Construct JSON data structure
                threat_data = {
                    "type": "clear_all_aggro",
                    "character": character_name,
                    "mob_name": "NA",
                    "threat": 0
                }

                # Construct JSON data structure
                threat_data = {
                    "type": "mob_slain",
                    "character": character_name,
                    "mob_name": mobName,
                    "threat": 0
                }
                
                # Construct JSON data structure
                threat_data = {
                    "type": threat_update,
                    "character": character_name,
                    "mob_name": mobName,
                    "threat": threat_value
                }
        '''

        # Construct JSON data structure
        threat_data = {
            "type": type,
            "character": character_name,
            "mob_name": mobName,
            "threat": threat_value,
        }

        # 构造JSON数据并编码为字节流
        body = json.dumps(threat_data).encode('utf-8')
        # 添加4字节大端序长度头
        size = len(body)
        header = size.to_bytes(4, byteorder='big')  # 生成4字节大端序长度头
        message = header + body  # 合并头和载荷


        try:
            total_sent = 0
            while total_sent < len(message):
                    sent = self.socket.send(message[total_sent:])
                    if sent == 0:
                        raise ConnectionError("Socket connection broken")
                    total_sent += sent
            self.logErrorMessage(f"Aggro table sent: {threat_data}", "info")

        except BlockingIOError:
            # 发送缓冲区满抛出BlockingIOError, 直接丢弃，等待下个周期再发，反正每次都是发全量的aggro table。
            self.logErrorMessage("Send buffer full, retrying later.", "info")
        except (ConnectionError, OSError) as e:
            self.logErrorMessage(f"Sending failed: {str(e)}","info")
            if self.socket:
                self.socket.close()
                self.socket = None
            self.socket_connected = False

        except Exception as e:
            self.logErrorMessage(f"Unexpected error: {str(e)}","info")


    def _emit_message_received(self, frame):
        # 这里实现消息转发逻辑
        self.logErrorMessage(f"Received message: {frame}","info")
        try:
            message = frame.decode('utf-8')
        except UnicodeDecodeError:
            self.logErrorMessage("Error decoding UTF-8 message", "info")
            return

        if hasattr(self, 'on_message_received'):
            self.on_message_received(message)


    def simulate_server_restart(self):
        """外部调用此方法模拟服务器重启，触发客户端重连"""
        if self.socket:
            self.socket.close()

            self.logErrorMessage("Connection closed manually to simulate server restart.", "info")



