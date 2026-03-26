package common

import (
	"encoding/csv"
	"fmt"
	"net"
	"os"
	"time"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID             string
	ServerAddress  string
	LoopAmount     int
	LoopPeriod     time.Duration
	BatchMaxAmount int
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

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop(signalChannel chan os.Signal) {
	filepath := fmt.Sprintf("/data/agency-%s.csv", c.config.ID)
	file, err := os.Open(filepath)
	if err != nil {
		log.Criticalf("action: open_file | result: fail | error: %v", err)
		return
	}
	defer file.Close()

	reader := csv.NewReader(file)

	if err := c.createClientSocket(); err != nil {
		return
	}

	for {
		select {
		case <-signalChannel:
			log.Infof("action: shutdown | result: success | client_id: %v", c.config.ID)
			return
		default:
			// Continue with the normal execution
		}

		batch, err := readBatch(reader, c.config.ID, c.config.BatchMaxAmount)
		if err != nil {
			log.Errorf("action: read_file | result: fail | error: %v", err)
			return
		}

		if len(batch) == 0 {
			break
		}

		// Send the batch to the server
		if err := SendMessage(serializeBatch(batch), c.conn); err != nil {
			log.Errorf("action: batch_enviado | result: fail | client_id: %v", c.config.ID)
			c.conn.Close()
			return
		}

		confirmation, err := ReceiveMessage(c.conn)
		if err != nil {
			log.Errorf("action: batch_enviado | result: fail | client_id: %v", c.config.ID)
			c.conn.Close()
			return
		}
		if confirmation == '0' {
			log.Errorf("action: batch_enviado | result: fail | client_id: %v", c.config.ID)
		} else {
			log.Infof("action: batch_enviado | result: success | client_id: %v", c.config.ID)
		}

		select {
		case <-signalChannel:
			log.Infof("action: shutdown | result: success | client_id: %v", c.config.ID)
			return
		case <-time.After(c.config.LoopPeriod):
		}

	}
	c.conn.Close()
	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}
