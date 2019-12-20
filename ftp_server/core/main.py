__author__ = 'Hugee'


import  socketserver,json
import os

class MyTCPHandler(socketserver.BaseRequestHandler):

    def get(self,*args):
        file_msg = args[0]
        filename = file_msg["filename"]
        # local_filesize = file_msg["size"]
        if os.path.isfile( filename): # 检查文件正确与否
            self.request.send("201".encode()) #201 命令可以执行
            status_code = self.request.recv(1024)
            filesize = os.stat(filename).st_size

            if status_code.decode() == "403":      # 客户端文件以存在,判断是否断点续传
                # print("将从文件暂停点进行数据下载...")
                self.request.send("000".encode())
                has_send_size = self.request.recv(1024).decode()
                has_send_size = int(has_send_size)
                #客户端文件不完整续传
                if has_send_size < filesize:
                    print("将从文件暂停点进行数据下载...")
                    self.request.send("205".encode())
                    filesize -= has_send_size
                    response = self.request.recv(1024) #等待交互代码确认响应

                # 客户端完整不可续传，不提供下载
                else:
                    self.request.send("405".encode()) #405 不续传
                    # self.request.send("文件完整，无需进行下载...")
                    return

            #客户端不存在此文件
            elif status_code.decode() == "402":
                has_send_size = 0


            with open(filename,"rb") as file:
                self.request.send(str(filesize).encode())       #发送文件大小
                response = self.request.recv(1024)     #等待响应
                file.seek(has_send_size)
                # m = hashlib.md5()
                for line in file:
                    # m.update(line)
                    self.request.send(line)
                # else:print("文件传输完成")
            # self.conn.sendall(m.hexdigest().encode())

        else: self.request.send("402".encode())



    def put(self,*args):
        #对传入的关于文件信息的元组数据进行提取使字典格式
        file_msg = args[0]
        filename = file_msg["filename"]
        filesize = file_msg["size"]
        overridden = file_msg["overridden"]
        # limit_size = self.user_db["limitsize"] #磁盘额度
        # used_size = self.__getdirsize(self.home_path) #已用空间大小
        #对文件信息数据进行处理
        if os.path.isfile(filename):
            if overridden == False:
                f = open(filename + ".new","wb")
            else:
                f = open(filename,"wb")
        else:
            f = open(filename,"wb")
        received_data_size = 0
        #进行一次会话确认 防止粘包
        self.request.send(b"202")
        #开始数据接收
        while received_data_size < filesize:
            if filesize - received_data_size > 1024:
                size = 1024
            else:
                size = filesize - received_data_size
                print("last size: " ,size)

            data = self.request.recv(size)
            f.write(data)
            received_data_size += len(data)
        else:
            print("file [%s] has uploaded..." % filename)

    def ls(self,*args):
        self.__no_arg_comm(*args)

    def dir(self,*args):
        self.__no_arg_comm(*args)

    def __no_arg_comm(self,*args):
        args = args[0]
        # if len(args.split()) == 1:
        self.request.send("201".encode())
        reponse = self.request.recv(1024)
        # print(reponse)
        send_data = os.popen(args["action"]).read().encode()
        self.request.send(send_data)
        # else:
        #     self.request.send("401".encode())


    def handle(self):
        while True:
            try:
                self.data = self.request.recv(1024).strip()
                print("{} wrote:".format(self.client_address[0]))
                print(self.data)
                #b'{"overridden": true, "action": "put", "filename": "1.mp4", "size": 52632554}'

                file_msg = json.loads(self.data.decode())
                action = file_msg["action"]
                if hasattr(self,action):
                    #通过文件信息提取action，通过action执行不同的自身方法
                    func = getattr(self,action)
                    func(file_msg)
                else:self.request.send("401".encode())


            except ConnectionResetError as e:
                print("err",e)
                break

if __name__ == "__main__":
    HOST , PORT = "0.0.0.0",9999

    server = socketserver.ThreadingTCPServer((HOST,PORT),MyTCPHandler)
    # server = socketserver.ForkingTCPServer((HOST,PORT),MyTCPHandler)
    server.serve_forever()
