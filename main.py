import datetime
import json
import os
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import mimetypes
import pathlib
import threading


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        print(data)
        data_parse = urllib.parse.unquote_plus(data.decode())
        print(data_parse)
        data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
        print(data_dict)

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(('localhost', 5000))
            s.sendall(str(data_dict).encode())

        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())


def run_client(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ('localhost', 3000)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


def run_server(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    sock.bind(server)
    try:
        while True:
            data, address = sock.recvfrom(1024)
            data_decoded = data.decode().replace("'", '"').replace(", ", ",\n")
            if os.path.isfile("result.json"):
                result = f',\n{{"{datetime.datetime.now()}":\n{data_decoded}\n}},\n'
            else:
                result = f'{{\n\t"{datetime.datetime.now()}":\n{data_decoded}\n}},\n'
            file = open("/storage/data.json", "a")
            file.write(result)
            file.close()
            print(f'Received data: {data.decode()} from: {address}')
    except KeyboardInterrupt:
        print(f'Destroy server')
    finally:
        sock.close()


HOST = '127.0.0.1'
PORT = 3000



if __name__ == '__main__':
    server = threading.Thread(target=run_server, args=(HOST, 5000))
    client = threading.Thread(target=run_client)
    server.start()
    client.start()
    server.join()
    client.join()

    print('Done!')
