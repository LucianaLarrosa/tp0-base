package common

import (
	"net"
	"os"
	"time"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
	Bet           Bet
}

// Client Entity that encapsulates how
type Client struct {
	config ClientConfig
	conn   net.Conn
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {
	client := &Client{
		config: config,
	}
	return client
}

// CreateClientSocket Initializes client socket. In case of
// failure, error is printed in stdout/stderr and exit 1
// is returned
func (c *Client) createClientSocket() error {
	conn, err := net.Dial("tcp", c.config.ServerAddress)
	if err != nil {
		log.Criticalf(
			"action: connect | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
	}
	c.conn = conn
	return nil
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop(signalChannel chan os.Signal) {
	// There is an autoincremental msgID to identify every message sent
	// Messages if the message amount threshold has not been surpassed
	for i := 0; i < c.config.LoopAmount; i++ {
		// Create the connection the server in every loop iteration. Send an
		select {
		case <-signalChannel:
			log.Infof("action: shutdown | result: success | client_id: %v", c.config.ID)
			return
		default:
			// Continue with the normal execution
		}

		c.createClientSocket()

		// TODO: Modify the send to avoid short-write
		err := SendBet(c.config.Bet, c.conn)
		if err != nil {
			log.Errorf("action: apuesta_enviada | result: fail | dni: %s | numero: %s",
				c.config.Bet.Documento,
				c.config.Bet.Numero,
			)
			c.conn.Close()
			return
		}

		err = ReceiveConfirmation(c.conn)
		c.conn.Close()
		if err != nil {
			log.Errorf("action: apuesta_enviada | result: fail | dni: %s | numero: %s",
				c.config.Bet.Documento,
				c.config.Bet.Numero,
			)
			return
		}

		log.Infof("action: apuesta_enviada | result: success | dni: %s | numero: %s",
			c.config.Bet.Documento,
			c.config.Bet.Numero,
		)

		// Wait a time between sending one message and the next one
		time.Sleep(c.config.LoopPeriod)

	}
	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}
