import socket, sys

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((sys.argv[1],int(sys.argv[2])))
s.send(b'Helloooo')
s.close()
