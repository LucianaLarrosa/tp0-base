import socket
import logging
import signal
from common.server_protocol import receive_message, send_message
from common.utils import store_bets, deserialize_batch

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
        Accepts client connections sequentially and handles each one.
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
        Reads batches from client_sock in a loop until the client closes the connection.
        Responds with success or error for each batch. 
        Closes the socket in all cases.
        """

        try:
            while True:
                msg = receive_message(client_sock)
                if msg is None:
                    break
                bets, has_error = deserialize_batch(msg)
                store_bets(bets)
                if not has_error:
                    logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}')
                    send_message(client_sock, SUCCESS_MSG)
                else:
                    logging.error(f'action: apuesta_recibida | result: fail | cantidad: {len(bets)}')
                    send_message(client_sock, ERROR_MSG)
        except OSError as e:
            logging.error(f'action: receive_message | result: fail | error: {e}')
        finally:
            client_sock.close()

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
