import socket
import logging
import signal
import threading
import queue
from common.server_protocol import receive_message, send_message
from common.utils import store_bets, load_bets, has_won, deserialize_batch

MSG_TYPE_BATCH = 'B'
MSG_TYPE_END   = 'E'
MSG_TYPE_QUERY = 'Q'

MSG_SUCCESS = '1'
MSG_ERROR = '0'
MSG_WINNERS = 'W'
class Server:
    def __init__(self, port, listen_backlog, agencies):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._total_agencies = agencies
        self._agencies_done = 0
        self._winners = {} #agencyID: [winners]
        self._sorteo_event = threading.Event()
        self._lock = threading.Lock()
        self._queue = queue.Queue()
        self._workers = []

    def _worker(self):
        while True:
            sock = self._queue.get()
            if sock is None:
                break
            self.__handle_client_connection(sock)

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation

        finishes, servers starts to accept new connections again
        """

        # Handle signal to graceful shutdown
        signal.signal(signal.SIGTERM, self.__handle_sigterm)

        for _ in range(self._total_agencies):
            t = threading.Thread(target=self._worker)
            t.start()
            self._workers.append(t)

        try:
            while True:
                client_sock = self.__accept_new_connection()
                self._queue.put(client_sock)
        except OSError as e:
            logging.info('action: server_run | result: fail | error: {e}')

    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            msg_type, msg = receive_message(client_sock)
        except OSError as e:
            logging.error(f'action: receive_message | result: fail | error: {e}')
            client_sock.close()
            return
        
        if msg_type == MSG_TYPE_BATCH:
            self.__handle_batch(client_sock, msg)
        elif msg_type == MSG_TYPE_END:
            self.__handle_end(client_sock)
        elif msg_type == MSG_TYPE_QUERY:
            self.__handle_query(client_sock, msg)

    def __handle_batch(self, sock, msg):
        bets, has_error = deserialize_batch(msg)
        with self._lock:
            store_bets(bets)
        if not has_error:
            logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}')
            send_message(sock, MSG_SUCCESS, "")
        else:
            logging.info(f'action: apuesta_recibida | result: fail | cantidad: {len(bets)}')
            send_message(sock, MSG_ERROR, "")
        sock.close()

    def __handle_end(self, end_sock):
        with self._lock:
            self._agencies_done += 1
            is_last = self._agencies_done == self._total_agencies
        if is_last:
            self.__do_sorteo()
            self._sorteo_event.set()
        end_sock.close()

    def __handle_query(self, sock, agency_id):
        self._sorteo_event.wait()
        self.__notify_agency(sock, agency_id)
    
    def __do_sorteo(self):
        logging.info('action: sorteo | result: success')
        all_bets = list(load_bets())
        self.__get_winners(all_bets)

    def __notify_agency(self, sock, agency):
        winners = self._winners.get(agency, [])
        logging.info(f'action: send_winners | result: success | agency: {agency} | cant: {len(winners)}')
        send_message(sock, MSG_WINNERS, ','.join(winners))
        sock.close()

    def __get_winners(self, all_bets):
        for bet in all_bets:
            if has_won(bet):
                agency = str(bet.agency)
                self._winners[agency] = self._winners.get(agency, []) + [str(bet.document)]

    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info('action: accept_connections | result: in_progress')
        try:
            c, addr = self._server_socket.accept()
            logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        except OSError as e:
            logging.error(f'action: accept_connections | result:  fail | error: {e}')
            raise
        return c

    def __handle_sigterm(self, signum, frame):
        logging.info('action: shutdown_server | result: in_progress')
        self._server_socket.close()
        for _ in self._workers:
            self._queue.put(None)
        for t in self._workers:
            t.join()
        logging.info('action: shutdown_server | result: success')
