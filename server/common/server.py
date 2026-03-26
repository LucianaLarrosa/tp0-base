import socket
import logging
import signal
from common.server_protocol import receive_message, send_message
from common.utils import store_bets, deserialize_bet

SUCCESS_MSG = b'1'
ERROR_MSG = b'0'

class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)

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
        except OSError:
            logging.info('action: server_run | result: fail | error: {e}')

    def __handle_client_connection(self, client_sock):
        """
        Reads a bet from client_sock, stores it and responds with success or error.
        Closes the socket in all cases upon completion.
        """

        try:
            recv_string = receive_message(client_sock)
        except OSError as e:
            logging.error(f'action: receive_message | result: fail | error: {e}')
            client_sock.close()
            return
        
        bet = deserialize_bet(recv_string)
        if bet is None:
            logging.info(f'action: apuesta_almacenada | result: fail')
            send_message(client_sock, ERROR_MSG)
            client_sock.close()
            return
        
        store_bets([bet])
        logging.info(f'action: apuesta_almacenada | result: success | dni: {bet.document} | numero: {bet.number}')
        send_message(client_sock, SUCCESS_MSG)
        client_sock.close()

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
        """
        Closes the server socket on SIGTERM, causing accept() to raise OSError
        and allowing the main loop to exit cleanly.
        """

        logging.info('action: shutdown_server | result: in_progress')
        self._server_socket.close()
        logging.info('action: shutdown_server | result: success')
