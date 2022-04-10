import socket
import re
import select
import sys

class WSGIServer(object):
    def __init__(self):
        # 得到监听套接字
        self.tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_server_socket.bind(("", 7892))
        self.tcp_server_socket.listen(128)
        self.tcp_server_socket.setblocking(False)

        # 注册监听
        self.epl = select.epoll()
        self.epl.register(self.tcp_server_socket.fileno(), select.EPOLLIN)
		
        # 初始化 frame.applicaction
        sys.path.append("./dynamic")
        frame = __import__("mini_frame")
        self.application = getattr(frame, "application")




    def service_client(self, new_socket, request):
        """
        基于epoll 的客户端处理，如果是静态资源，则返回文件，如果是动态资源，则调用函数
        """
        request_lines = request.splitlines()  # 按照行切分

        print(request_lines[0])  # 得到每一行，其中第一行是 GET / HTTP/1.1
        ret = re.match(r"[^/]+(/[^ ]*)", request_lines[0])  # 正则匹配出路径 /html/index.html
        file_name = ret.group(1)  # 切分出的第一个结果就是
        # 这里特殊处理一下 / 路径，即：默认地址请求
        if file_name == "/":
            file_name = "/index.html"

        if not file_name.endswith(".html"):
            try:
                f = open("static" + file_name, "rb")
            except Exception as e:
                print(e)
                response_header = "HTTP/1.1 404 NOT FOUND\r\n"  # 请求失败的头部
                response_header += "\r\n"
                response_body = "<h1>404 NOT FOUND</h1>"
                response = (response_header + response_body).encode("utf-8")
                new_socket.send(response)
            else:
                response_header = "HTTP/1.1 200 OK\r\n"  # 请求成功的请求头
                response_body = f.read()
                response_header += "Content-Length:%d\r\n" % len(response_body)  # 长连接需要使用Length
                response_header += "\r\n"
                response = response_header.encode("utf-8") + response_body
                new_socket.send(response)
                f.close()
        else:  # 如果以.html结尾，是伪静态请求，交给frame.application处理
            response_body = self.application(file_name)
            response_header = "HTTP/1.1 200 OK\r\n"  # 请求成功的请求头
            response_header += "Content-Length:%d\r\n" % len(response_body)  # 长连接需要使用Length
            response_header += "\r\n"
            response = (response_header + response_body).encode("utf-8")
            new_socket.send(response)
			
    def run(self):
        event_dict = dict()
        while True:
            event_list = self.epl.poll()
            for f_no, event in event_list:
                if f_no == self.tcp_server_socket.fileno():
                    new_socket, client_addr = self.tcp_server_socket.accept()
                    self.epl.register(new_socket.fileno(), select.EPOLLIN)
                    # 将连接套接字注册，并且另存一份到字典
                    event_dict[new_socket.fileno()] = new_socket
                else:
                    # 如果是连接套接字，说明有信息发送过来了，对信息进行处理
                    new_socket = event_dict[f_no]  # 取出通知的连接套接字
                    request = new_socket.recv(1024).decode("utf-8")
                    if request:
                        # 如果不是断开连接请求，处理
                        self.service_client(new_socket, request)
                    else:
                        # 如果是断开连接请求，移除poll中的注册，移除字典中数据
                        self.epl.unregister(f_no)
                        event_dict[f_no].close()
                        del event_dict[f_no]

if __name__ == "__main__":
    wsgi_server = WSGIServer()
    wsgi_server.run()
