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
        self._lock = threading.Lock()
        self._condition = threading.Condition()
        self._sorteo_done = False
        self._queue = queue.Queue()
        self._workers = []

    def _worker(self):
        # Worker loop: reads sockets from the queue and handles each connection.
        # Exits when it receives None as the shutdown signal.
        while True:
            sock = self._queue.get()
            if sock is None:
                break
            self.__handle_client_connection(sock)

    def run(self):
        """
        Starts the worker pool and accepts connections, enqueueing each one for processing.
        Registers SIGTERM handler for graceful shutdown.
        Exits when the server socket is closed (OSError).
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
        Reads typed messages from client_sock in a loop.
        Dispatches to the appropriate handler based on message type.
        Exits the loop on END or QUERY. Closes the socket on error.
        """

        try:
            while True:
                msg_type, msg = receive_message(client_sock)
                if msg_type == MSG_TYPE_BATCH:
                    self.__handle_batch(client_sock, msg)
                elif msg_type == MSG_TYPE_END:
                    self.__handle_end(client_sock)
                    break
                elif msg_type == MSG_TYPE_QUERY:
                    self.__handle_query(client_sock, msg)
                    break
        except OSError as e:
            logging.error(f'action: receive_message | result: fail | error: {e}')
            client_sock.close()
        
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

    def __handle_end(self, end_sock):
        with self._condition:
            self._agencies_done += 1
            if self._agencies_done == self._total_agencies:
                self.__do_sorteo()
                self._sorteo_done = True
                self._condition.notify_all()
        end_sock.close()

    def __handle_query(self, sock, agency_id):
        with self._condition:
            self._condition.wait_for(lambda: self._sorteo_done)
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
        Blocks until a new client connection is accepted. Returns the client socket.
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
        """
        Closes the server socket and signals all workers to stop by enqueueing None.
        Joins all worker threads before returning.
        """

        logging.info('action: shutdown_server | result: in_progress')
        self._server_socket.close()
        for _ in self._workers:
            self._queue.put(None)
        for t in self._workers:
            t.join()
        logging.info('action: shutdown_server | result: success')
