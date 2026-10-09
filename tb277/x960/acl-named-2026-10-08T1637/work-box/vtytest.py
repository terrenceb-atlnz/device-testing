import socket, sys
# TCP connect to the DUT's vty port from a chosen SOURCE address.
# ACCEPTED = the vty access-class let this source in; REFUSED/TIMEOUT = it did not.
src, dst, port = sys.argv[1], sys.argv[2], int(sys.argv[3])
s = socket.socket(); s.settimeout(6)
try:
    s.bind((src, 0)); s.connect((dst, port))
    data = s.recv(100)
    print('%-14s -> ACCEPTED  banner=%r' % (src, data[:30]))
except socket.timeout:
    print('%-14s -> TIMEOUT (blocked)' % src)
except ConnectionRefusedError:
    print('%-14s -> REFUSED (blocked)' % src)
except Exception as e:
    print('%-14s -> %s' % (src, type(e).__name__))
finally:
    s.close()
