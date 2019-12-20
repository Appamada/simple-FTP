__author__ = 'Hugee'

import socket,hashlib,os
import json,sys


class FTP_client(object):
    def __init__(self):
       self.client = socket.socket()

    def help(self):
        msg='''
        ls
        pwd
        cd
        get [filename]
        put [filename]
        '''

        status_code = '''
        400 用户认证失败
        401 命令不正确
        402 文件不存在
        403 创建文件已经存在
        404 磁盘空间不够
        405 不续传

        200 用户认证成功
        201 命令可以执行
        202 磁盘空间够用
        203 文件具有一致性
        205 续传

        000 系统交互码
        '''
        print("可用指令:\n",msg)
        print("状态码:\n",status_code)

    def connection(self,ip,port):
        self.client.connect((ip,port))

    def start(self):
        self.connection()
        while True:
            username = input("输入用户名: ").strip
            password = input("输入密码: ").strip
            login_info = ("%s:%s" % (username,password))
            self.client.send(login_info.encode())
            status_code = self.client.recv(1024).decode()
            if status_code == "400":
                print("[%s]用户名密码认证错误" % status_code)
                continue
            else:print("[%s]用户密码认证成功" % status_code)
            self.interactive()

    def interactive(self):
        while True:
            cmd = input(">>").strip()
            if len(cmd) == 0 :
                continue
            cmd_comm = cmd.split()[0]
            if hasattr(self,"cmd_%s" % cmd_comm):
                #获取方法的内存地址并指向一个变量名
                func = getattr(self,"cmd_%s" % cmd_comm)
                func(cmd)
            else:
                print("[%s]命令不存在" % 401)
                self.help()



    def cmd_put(self,*args):
        cmd_split = args[0].split()
        if len(cmd_split) > 1:
            filename = cmd_split[1]
            if os.path.isfile(filename):
                filesize = os.stat(filename).st_size

                msg_dic = {
                    "filename":filename,
                    "size":filesize,
                    "overridden":True,
                    "action":"put"
                }

                attr = json.dumps(msg_dic).encode()
                self.client.send(attr)
                # 两次send写在一起为防止粘包进行一次交互确认
                status_code = self.client.recv(1024).decode()
                print(status_code)
                if status_code == "202":
                # 开始传输文件
                    f = open(filename,"rb")
                    for line in f:
                        send_size = f.tell()
                        self.client.send(line)
                        self.__progress(send_size, filesize, "上传中")
                    else:
                        print("\nthe file [%s] is uploaded." % filename)
                    # status_code = self.client.recv(1024).decode()
                    # if status_code == "203":
                    #     print("\n文件具有一致性")
                else:print("[%s] Erro! " % (status_code))

            else:
                print("[401 Erro]")
        else:
            print("[401 Error]")


    def cmd_get(self,*args):
        cmd_split = args[0].split()
        filename = cmd_split[1]
        # print(cmd_split)
        if len(cmd_split) > 1:
            # filesize = os.stat(filename).st_size

            msg_dic = {
                "filename":filename,
                "action":"get"
                # "size" : filesize
            }

            attr = json.dumps(msg_dic).encode()
            self.client.send(attr)
            status_code = self.client.recv(1024)
            if status_code.decode() == "201":
                if os.path.isfile(filename): #检查文件是否在本地存在
                    self.client.send("403".encode()) #文件已存在
                    self.client.recv(1024)
                    existed_file_size = os.stat(filename).st_size
                    #将文件大小传过去
                    self.client.send(str(existed_file_size).encode())
                    status_code = self.client.recv(1024).decode()

                    if status_code == "205": # 205 续传
                        print("开始续传文件")
                        self.client.send("000".encode())
                        file_total_size = self.client.recv(1024)
                        file_total_size = int(file_total_size.decode())
                        self.client.send("000".encode())

                        while existed_file_size < file_total_size:
                            f = open(filename,"ab")
                            data = self.client.recv(1024)
                            existed_file_size += len(data)
                            f.write(data)
                            self.__progress(existed_file_size,file_total_size,"下载中")
                        else:
                            print("文件续传完成")
                            return


                    elif status_code == "405":
                        print("文件已存在，且大小一致，无需再下载")
                        return

                else:
                    self.client.send("402".encode()) #文件不存在
                    filesize = 0
                    file_total_size = self.client.recv(1024)
                    file_total_size = int(file_total_size.decode())
                    self.client.send("000".encode())
                    print(file_total_size)
                    while  filesize < file_total_size:
                        f = open(filename,"ab")
                        data = self.client.recv(1024)
                        filesize += len(data)
                        f.write(data)
                        self.__progress(filesize,file_total_size,"下载中")
                    else:
                        print("下载完成")
                        return

            else:
                # print(1)
                print("Error [%s]" % status_code)




    def cmd_ls(self,*args):
        self.__universal_method_none(*args)
        pass

    def cmd_dir(self,*args):
        self.__universal_method_none(*args)

    def cmd_cd(self,*args):
        pass

    def __progress(self, trans_size, file_size, mode):
        '''
        :param trans_size:已经传输的数据大小
        :param file_size: 文件的总大小
        :param mode: 模式
        '''
        bar_length = 100
        percent = float(trans_size)/float(file_size)
        hashes = "#" * int(percent * bar_length)
        spaces = " " * (bar_length - len(hashes))
        sys.stdout.write(
            "\r%s:%.2fM/%.2fM %d%% [%s]"%(mode,trans_size/1048576,file_size/1048576,percent*100,hashes+spaces))
        sys.stdout.flush()


    def __universal_method_none(self,*args):
        args = args[0]
        msg_dic = {
            "action": args,
        }
        # print(args)
        self.client.send(json.dumps(msg_dic).encode())
        status_code = self.client.recv(1024).decode()
        if status_code == "201":
            self.client.send("000".encode())
            data = self.client.recv(1024).decode()
            print(data)
        else:
            print("[%s] Error!" % (status_code))


ftp = FTP_client()
ftp.connection("localhost",9999)
# ftp.connection("192.168.100.130",9999)
ftp.interactive()