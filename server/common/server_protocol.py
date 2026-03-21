MSG_CONFIRMATION = '1'
MSG_ERROR = '0'
MSG_WINNERS = 'W'

def send_message(sock, msg_type, body):
    msg = f"{msg_type}{len(body):04d}{body}".encode()
    n_sent = 0
    while n_sent < len(msg):
        n = sock.send(msg[n_sent:])
        n_sent += n

def send_confirmation(sock):
    send_message(sock, MSG_CONFIRMATION, "")

def send_error(sock):
    send_message(sock, MSG_ERROR, "")

def send_winners(sock, winners):
    msg = ','.join(winners)
    send_message(sock, MSG_WINNERS, msg)

def receive_message(sock):
    header = b''
    while len(header) < 5:
        n_recv = sock.recv(5-len(header))
        if not n_recv:
            return None
        header += n_recv
    
    msg_type = chr(header[0])
    msg_len = int(header[1:5].decode())
    msg = b''
    while len(msg) < msg_len:
        msg_recv = sock.recv(msg_len - len(msg))
        if not msg_recv:
            return None
        msg += msg_recv
    return msg_type, msg.decode()
