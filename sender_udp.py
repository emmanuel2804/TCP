import socket, sys

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
to = (sys.argv[1],int(sys.argv[2]))
s.sendto(b'Helloooo', to)
s.close()
