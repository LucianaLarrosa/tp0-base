from common.utils import Bet

def send_confirmation(sock):
    msg = b'1'
    sent = 0
    while sent < len(msg):
        n = sock.send(msg[sent:])
        sent += n

def receive_batch(sock):
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
    lines = msg_recv.decode().strip().split('\n')
    bets = []
    for line in lines:
        fields = line.split(',')
        bets.append(Bet(fields[0], fields[1], fields[2], fields[3], fields[4], fields[5]))
    return bets