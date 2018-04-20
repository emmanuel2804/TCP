import socket

from netifaces import interfaces, ifaddresses, AF_INET

ip = '127.0.0.1'

for ifacename in interfaces():
    for add in ifaddresses(ifacename).setdefault(AF_INET, [{'addr':'00'}]):
        if add['addr'] != '00' and add['addr']!='lo0':
            ip = add['addr']

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

s.bind((ip, 2000))

data, sender = s.recvfrom(1024)
print("{} sent:\n".format(sender))
print(data.decode())
s.close()
