package common

import (
	"fmt"
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

// createClientSocket connects to the server with up to 5 retries.
// On success, stores the connection in c.conn.
func (c *Client) createClientSocket() error {
	maxRetries := 5
	for i := 0; i < maxRetries; i++ {
		conn, err := net.Dial("tcp", c.config.ServerAddress)
		if err == nil {
			c.conn = conn
			return nil
		}
		log.Infof("action: connect | result: in_progress | client_id: %v | attempt: %v", c.config.ID, i+1)
		time.Sleep(500 * time.Millisecond)
	}
	log.Criticalf("action: connect | result: fail | client_id: %v", c.config.ID)
	return fmt.Errorf("Could not connect after %d retries", maxRetries)
}

// StartClientLoop sends the configured bet to the server repeatedly,
// once per loop iteration with a delay between each.
// Stops early on SIGTERM or communication error.
func (c *Client) StartClientLoop(signalChannel chan os.Signal) {
	for i := 0; i < c.config.LoopAmount; i++ {
		select {
		case <-signalChannel:
			log.Infof("action: shutdown | result: success | client_id: %v", c.config.ID)
			return
		default:
			// Continue with the normal execution
		}

		if err := c.createClientSocket(); err != nil {
			return
		}

		msg := serializeBet(c.config.Bet)
		err := SendMessage(msg, c.conn)
		if err != nil {
			log.Error("action: send_message | result: fail")
			c.conn.Close()
			return
		}

		confirmation, err := ReceiveMessage(c.conn)
		c.conn.Close()
		if err != nil || confirmation == '0' {
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

		select {
		case <-signalChannel:
			log.Infof("action: shutdown | result: success | client_id: %v", c.config.ID)
			return
		case <-time.After(c.config.LoopPeriod):
		}

	}
	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}
