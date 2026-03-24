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
            bets, has_error = deserialize_batch(msg)
            store_bets(bets)
            if not has_error:
                logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}')
                send_message(client_sock, MSG_SUCCESS, "")
            else:
                logging.info(f'action: apuesta_recibida | result: fail | cantidad: {len(bets)}')
                send_message(client_sock, MSG_ERROR, "")
            client_sock.close()
        elif msg_type == MSG_TYPE_END:
            self._agencies_done += 1
            if self._agencies_done == self._total_agencies:
                logging.info('action: sorteo | result: success')
                all_bets = list(load_bets())
                for agency, sock in self._waiting_agencies.items():
                    winners = self.__get_winners(agency, all_bets)
                    logging.info(f'action: send_winners | result: success | agency: {agency} | cant: {len(winners)}')
                    send_message(sock, MSG_WINNERS, ','.join(winners))
                    sock.close()
                self._waiting_agencies.clear()
            client_sock.close()
        elif msg_type == MSG_TYPE_QUERY:
            agency_id = msg
            if self._agencies_done == self._total_agencies:
                all_bets = list(load_bets())
                winners = self.__get_winners(agency_id, all_bets)
                logging.info(f'action: send_winners | result: success | agency: {agency_id} | cant: {len(winners)}')
                send_message(client_sock, MSG_WINNERS, ','.join(winners))
                client_sock.close()
            else:
                self._waiting_agencies[agency_id] = client_sock

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
