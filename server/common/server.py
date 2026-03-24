import socket
import logging
import signal
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
        self._waiting_agencies = {} #agencyID: socket
        self._winners = {} #agencyID: [winners]

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation

        finishes, servers starts to accept new connections again
        """

        # Handle signal to graceful shutdown
        signal.signal(signal.SIGTERM, self.__handle_sigterm)

        try:
            while True:
                client_sock = self.__accept_new_connection()
                self.__handle_client_connection(client_sock)
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
        store_bets(bets)
        if not has_error:
            logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}')
            send_message(sock, MSG_SUCCESS, "")
        else:
            logging.info(f'action: apuesta_recibida | result: fail | cantidad: {len(bets)}')
            send_message(sock, MSG_ERROR, "")
        sock.close()

    def __handle_end(self, end_sock):
        self._agencies_done += 1
        if self._agencies_done == self._total_agencies:
            self.__do_sorteo()
            for agency, sock in self._waiting_agencies.items():
                self.__notify_agency(sock, agency)
            self._waiting_agencies.clear()
        end_sock.close()

    def __handle_query(self, sock, agency_id):
        if self._agencies_done == self._total_agencies:
            self.__notify_agency(sock, agency_id)
        else:
            self._waiting_agencies[agency_id] = sock
    
    def __do_sorteo(self):
        logging.info('action: sorteo | result: success')
        all_bets = list(load_bets())
        for i in range(1, self._total_agencies + 1):
            self._winners[str(i)] = self.__get_winners(str(i), all_bets)

    def __notify_agency(self, sock, agency):
        winners = self._winners[agency]
        logging.info(f'action: send_winners | result: success | agency: {agency} | cant: {len(winners)}')
        send_message(sock, MSG_WINNERS, ','.join(winners))
        sock.close()

    def __get_winners(self, agency_id, all_bets):
        winners = []
        for bet in all_bets:
            if has_won(bet) and int(bet.agency) == int(agency_id):
                winners.append(str(bet.document))
        return winners

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
        logging.info('action: shutdown_server | result: success')
