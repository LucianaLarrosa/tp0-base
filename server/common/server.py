import socket
import logging
import signal
from common.server_protocol import send_confirmation, receive_message, send_error
from common.utils import store_bets, deserialize_bet


class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)

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
        except OSError:
            logging.info('action: server_run | result: fail | error: {e}')

    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            recv_string = receive_message(client_sock)
            bet = deserialize_bet(recv_string)
            store_bets([bet])
            logging.info(f'action: apuesta_almacenada | result: success | dni: {bet.document} | numero: {bet.number}')
            send_confirmation(client_sock)
        except OSError as e:
            logging.error(f'action: receive_message | result: fail | error: {e}')
        except Exception as e:
            logging.info(f'action: apuesta_almacenada | result: fail | error: {e}')
            send_error(client_sock)
        finally:
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
        logging.info('action: shutdown_server | result: in_progress')
        self._server_socket.close()
        logging.info('action: shutdown_server | result: success')
