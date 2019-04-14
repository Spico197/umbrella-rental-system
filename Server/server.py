import socket
import time
import json
import threading
import logging
import datetime
import os
import sys
import inspect
import ctypes

from django import setup as django_setup
sys.path.insert(0, os.path.abspath(os.path.dirname(os.getcwd())))
os.environ['DJANGO_SETTINGS_MODULE'] = 'UmbrellaRentalSystemWeb.settings'
django_setup()

from umbrella.models import Umbrella, UmbrellaShelf2Position, UmbrellaShelf

"""
clients = [
    {"address": address, "client": client, "shelf": UmbrellaShelf(), "thread": StuckThread()},
    {"address": address, "client": client, "shelf": UmbrellaShelf(), "thread": StuckThread()},
]
"""
clients = []

logging.basicConfig(filename="routine-log.txt",
                    filemode="a",
                    format='%(asctime)s - %(levelname)s - %(message)s')

def get_native_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class StuckThreadMeta(threading.Thread):
    def __init__(self, **kwargs):
        super().__init__()
        self.client = kwargs['client']
        self.address = kwargs['address']
        self.timeout = kwargs['timeout']
        self.wait_time = kwargs['wait_time']

        self.client.settimeout(self.wait_time)

    def sendall(self, data):
        try:
            self.client.sendall(data)
        except ConnectionError as err:
            print(f"[ {get_native_time()} ]: ConnectionError: {self.address}")
            logging.error(f"ConnectionError: {self.address}")
            self.close()
        except OSError as err:
            if isinstance(err, socket.timeout):
                raise socket.timeout
            else:
                print(f"[ {get_native_time()} ]: OSError: {self.address}")
                logging.error(f"OSError: {self.address}")
                self.close()

    def recv(self, buffer_size=1024):
        try:
            return self.client.recv(buffer_size)
        except ConnectionError as err:
            print(f"[ {get_native_time()} ]: ConnectionError: {self.address}")
            logging.error(f"ConnectionError: {self.address}")
            self.close()
        except OSError as err:
            if isinstance(err, socket.timeout):
                raise socket.timeout
            else:
                print(f"[ {get_native_time()} ]: OSError: {self.address}")
                logging.error(f"OSError: {self.address}")
                self.close()

    def close(self):
        global clients
        logging.info(f"[ {get_native_time()} ]: Close Client: {self.address}")
        for client in clients:
            if client['client'] == self.client:
                clients.remove(client)
                break
        if self.client._closed is False:
            self.client.close()


class StuckThread(StuckThreadMeta):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.borrow_timer = None
        self.borrow_ack = False
        self.kwargs = kwargs
        print(kwargs)
    
    def run(self):
        while True:
            try:
                read_bytes = self.recv()
                if len(read_bytes) == 1:
                    read_bytes += self.recv()
                response_json = json.loads(read_bytes.decode())
                print('收到请求: ', response_json)
                if verify_shelf(response_json):
                    if response_json['action']['number'] == 2 and \
                        response_json['action']['pos_id'] and response_json['action']['umbrella_uid']:
                        try:
                            print('收到还伞请求: ', response_json)
                            pos = UmbrellaShelf2Position.objects.get(pk=response_json['action']['pos_id'])
                            umbrella = Umbrella.objects.get(uid__exact=response_json['action']['umbrella_uid'])
                            pos.status = '1'
                            pos.umbrella = umbrella
                            umbrella.status = '1'
                            umbrella.save()
                            pos.save()
                        except Exception as err:
                            print('错误: ', err, response_json)
                        finally:
                            msg = {
                                "heart": False,
                                "connection": True,
                                "ack": True,
                                "action": {
                                    "number": 2,
                                    "pos_id": int(response_json['action']['pos_id']),
                                    "umbrella_id": umbrella.id
                                }
                            }
                            print('发送还伞确认: ', msg)
                            self.sendall(json.dumps(msg).encode())
                    elif response_json['action']['number'] == 1 and response_json['ack'] is True:
                        self.borrow_timer = None
                        print('收到借伞确认')
                        self.borrow_ack = True
                if self.borrow_timer:
                    time_delta = time.time() - self.borrow_timer
                    if time_delta > 5.0:
                        print('client {} lost'.format(self.kwargs))
                        break
            except Exception as err:
                if isinstance(err, socket.timeout):
                    pass
                else:
                    raise err


    def server_borrow(self, shelf_id, pos_id):
        if self.kwargs['shelf_id'] == shelf_id:
            msg = {
                "heart": False,
                "connection": True,
                "ack": False,
                "action": {
                    "number": 1,
                    "pos_id": pos_id,
                    "umbrella_id": -1
                }
            }
            print('发送借伞请求: ', msg)
            self.sendall(json.dumps(msg).encode())
            self.borrow_ack = False
            self.borrow_timer = time.time()
            for i in range(5):
                if self.borrow_ack is True:
                    return True
                time.sleep(1)
        return False
    
    def __del__(self):
        self.close()


def verify_shelf(msg):
    try:
        shelf = UmbrellaShelf.objects.get(id__exact=msg['shelf']['id'], 
                                          identify_code__exact=msg['shelf']['code'])
        if shelf:
            return True
    except Exception:
        return False


def borrow_umbrella(shelf_id, pos_id):
    global clients
    print('client id: ', id(clients))
    print(clients)
    for client in clients:
        if client['shelf_id'] == shelf_id:
            print('找到client')
            return client['thread'].server_borrow(shelf_id, pos_id)
    return False


def _async_raise(tid, exctype):
    """raises the exception, performs cleanup if needed"""
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


def stop_thread(thread):
    _async_raise(thread.ident, SystemExit)


def inner_com(client, address):
    try:
        recv_string = client.recv(1024)
        recv = json.loads(recv_string.decode())
        send_string = json.dumps({"result": borrow_umbrella(recv['shelf_id'], recv['pos_id'])})
    except:
        send_string = json.dumps({"result": False})
    finally:
        client.sendall(send_string.encode())


def inner_server(ip, port):
    inner_server = socket.socket()
    inner_server.bind((ip, port))
    inner_server.listen(10)
    while True:
        inner_client, inner_address = inner_server.accept()
        inner_client.settimeout(5)
        handle = threading.Thread(target=inner_com, args=(inner_client, inner_address))
        handle.start()


if __name__ == '__main__':
    ip_port = ('0.0.0.0', 65432)
    max_listen_num = 100  # 最大连接数为10
    timeout = 60  # 心跳间隔为30秒
    wait_time = 5  # 阻塞式方法等待响应时间(秒)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 面向Internet的流式套接字
    server.bind(ip_port)  # 绑定地址
    server.listen(max_listen_num)  # 开始监听
    print('{} Server - {}:{} Listening {}'.format('-' * 20, ip_port[0], ip_port[1], '-' * 20))
    # global clients
    def main_thread_entrance(max_listen_num, timeout, wait_time):
        while True:
            # 直到达到最大连接数为止, 不断尝试建立新的连接
            if len(clients) >= max_listen_num:
                continue
            client, address = server.accept()
            try:
                client.settimeout(wait_time)
                con_ok_bytes = client.recv(1024)
                if len(con_ok_bytes) == 1:
                    con_ok_bytes += client.recv(1024)
                print(con_ok_bytes)
                con_ok_json = json.loads(con_ok_bytes.decode())
                if verify_shelf(con_ok_json):
                    shelf = UmbrellaShelf.objects.get(pk=con_ok_json['shelf']['id'])
                    if shelf.capacity != 0:
                        response_json = {
                            "heart": False,
                            "ack": True,
                            "connection": True,
                            "action": {
                                "number": -1,
                                "pos_id": -1,
                                "umbrella_id": -1
                            }
                        }
                        client.sendall(json.dumps(response_json).encode())
                        param = {
                            "client": client,
                            "address": address,
                            "timeout": timeout,
                            "wait_time": wait_time,
                            "shelf_id": shelf.id,
                        }
                        stuck_thread = StuckThread(**param)
                        clients.append({"client": client, "address": address, "shelf_id": shelf.id, "thread": stuck_thread})
                        stuck_thread.start()
            except Exception as err:
                print(err, 'client: {}, address: {} connection failed!'.format(client, address))

    handle = threading.Thread(target=main_thread_entrance, args=(max_listen_num, timeout, wait_time))
    handle.start()

    handle_inner = threading.Thread(target=inner_server, args=('localhost', 65431))
    handle_inner.start()

    while True:
        cmd = input(">>> ")
        if cmd == 'number':
            print("The number of clients: {}".format(len(clients)))
        elif cmd == 'list':
            print('clients id:', id(clients))
            for client in clients:
                print(client)
        elif cmd == 'borrow_test':
            print(borrow_umbrella(5, 7))
        elif cmd == "quit":
            for client in clients:
                if not client['client']._closed:
                    client['client'].close()
                stop_thread(client['thread'])
            stop_thread(handle)
            print("Bye")
            break
    print('you can close now...')
