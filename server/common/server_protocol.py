from common.utils import Bet

def send_confirmation(sock):
    msg = b'1'
    sent = 0
    while sent < len(msg):
        n = sock.send(msg[sent:])
        sent += n

def receive_bet(sock):
    len_recv_byte = b''
    while len(len_recv_byte) < 4:
        bytes_recv = sock.recv(4 - len(len_recv_byte))
        if not bytes_recv:
            return None
        len_recv_byte += bytes_recv
    msg_len = int(len_recv_byte.decode())
    msg_recv = b''
    while len(msg_recv) < msg_len:
        bytes_recv = sock.recv(msg_len - len(msg_recv))
        if not bytes_recv:
            return None
        msg_recv += bytes_recv
    bet = msg_recv.decode().split(',')
    return Bet(bet[0], bet[1], bet[2], bet[3], bet[4], bet[5])