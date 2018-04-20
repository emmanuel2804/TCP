from RawUSocket import RawSocket
import sys

ip_dst, port_dst = sys.argv[1], sys.argv[2]

s = RawSocket('h1-eth0')
#s = RawSocket('enp0s3')
s.sendto((ip_dst, int(port_dst)), 'no mistake, this is the data')
