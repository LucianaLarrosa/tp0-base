import socket
import logging
import signal
import threading
from common.server_protocol import send_confirmation, send_error, send_winners, receive_message
from common.utils import store_bets, Bet, load_bets, has_won

MSG_TYPE_BATCH = 'B'
MSG_TYPE_END   = 'E'
MSG_TYPE_QUERY = 'Q'
class Server:
    def __init__(self, port, listen_backlog, agencies):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._total_agencies = agencies
        self._agencies_done = 0
        self._waiting_agencies = {} #agencyID: socket
        self._lock = threading.Lock()

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        # TODO: Modify this program to handle signal to graceful shutdown
        # the server DONE!!
        signal.signal(signal.SIGTERM, self.__handle_sigterm)

        try:
            while True:
                client_sock = self.__accept_new_connection()
                thread = threading.Thread(target=self.__handle_client_connection, args=(client_sock,))
                thread.start()
        except OSError as e:
            logging.info('action: server_run | result: fail | error: {e}')

    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        bets = []
        try:
            msg_type, msg = receive_message(client_sock)
            if msg_type == MSG_TYPE_BATCH:
                lines = msg.strip().split('\n')
                for line in lines:
                    fields = line.split(',')
                    bet = Bet(fields[0], fields[1], fields[2], fields[3], fields[4], fields[5])
                    bets.append(bet)
                with self._lock:
                    store_bets(bets)
                logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}')
                send_confirmation(client_sock)
            elif msg_type == MSG_TYPE_END:
                with self._lock:
                    self._agencies_done += 1
                    if self._agencies_done == self._total_agencies:
                        logging.info('action: sorteo | result: success')
                        all_bets = list(load_bets())
                        for agency, sock in self._waiting_agencies.items():
                            winners = self.__get_winners(agency, all_bets)
                            logging.info(f'action: send_winners | result: success | agency: {agency} | cant: {len(winners)}')
                            send_winners(sock, winners)
                            sock.close()
                        self._waiting_agencies.clear()
            elif msg_type == MSG_TYPE_QUERY:
                agency_id = msg
                with self._lock:
                    if self._agencies_done == self._total_agencies:
                        all_bets = list(load_bets())
                        winners = self.__get_winners(agency_id, all_bets)
                        logging.info(f'action: send_winners | result: success | agency: {agency_id} | cant: {len(winners)}')
                        send_winners(client_sock, winners)
                    else:
                        self._waiting_agencies[agency_id] = client_sock
        except Exception as e:
            logging.error(f'action: apuesta_recibida | result: fail | cantidad: {len(bets)}')
            send_error(client_sock)
        finally:
            if client_sock not in self._waiting_agencies.values():
                client_sock.close()

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
