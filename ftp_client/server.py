

import socket,os,time

server = socket.socket()
server.bind(("localhost",9999))

server.listen(5)

while True:
    conn,addr = server.accept()
    print("new conn:",conn)

    while True:
        data = conn.recv(1024)
        if len(data) == 0:
            print("the client has lost ...")
            break
        print("recv",data)
        # print(len(data))
        print("执行指令",data)
        cmd_res = os.popen(data.decode()).read()
        if not cmd_res:
            cmd_res = "cmd can't find..."
        print("before send",len(cmd_res)) #增加一次交互使得粘包问题解决
        # print(cmd_res)
        conn.send(str(len(cmd_res.encode())).encode("utf-8")) #如果不对命令结果encode后在计算长度，则字符串的1中文字符为1，导致与data的实际长度出现偏差
        # time.sleep(0.5) #sleep不能实时
        client_ack = conn.recv(1024)
        print(client_ack.decode())
        conn.send(cmd_res.encode("utf-8"))
        print("send done...")

server.close()

