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
        Accepts client connections and handles each one.
        Registers SIGTERM handler for graceful shutdown.
        Exits when the server socket is closed (OSError).
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
        store_bets(bets)
        if not has_error:
            logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}')
            send_message(sock, MSG_SUCCESS, "")
        else:
            logging.info(f'action: apuesta_recibida | result: fail | cantidad: {len(bets)}')
            send_message(sock, MSG_ERROR, "")

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
        Closes the server socket on SIGTERM, causing accept() to raise OSError
        and allowing the main loop to exit cleanly.
        """

        logging.info('action: shutdown_server | result: in_progress')
        self._server_socket.close()
        logging.info('action: shutdown_server | result: success')
