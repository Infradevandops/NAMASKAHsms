package namaskah

import (
	"bytes"
	"encoding/json"
	"io"
	"net/http"
	"time"
)

type Config struct {
	APIKey  string
	BaseURL string
	Timeout time.Duration
}

type Client struct {
	httpClient *http.Client
	config     Config
	Verify     *VerifyService
	Forwarding *ForwardingService
	Users      *UsersService
	Referrals  *ReferralsService
}

func NewClient(config Config) *Client {
	if config.BaseURL == "" {
		config.BaseURL = "https://api.namaskah.com/api"
	}
	if config.Timeout == 0 {
		config.Timeout = 10 * time.Second
	}

	c := &Client{
		httpClient: &http.Client{
			Timeout: config.Timeout,
		},
		config: config,
	}

	// Services are initialized in NewClient
	c.Verify = &VerifyService{client: c}
	c.Forwarding = &ForwardingService{client: c}
	c.Users = &UsersService{client: c}
	c.Referrals = &ReferralsService{client: c}

	return c
}

func (c *Client) doRequest(method, path string, body interface{}, params map[string]string) (*http.Response, error) {
	var bodyReader io.Reader
	if body != nil {
		jsonData, err := json.Marshal(body)
		if err != nil {
			return nil, err
		}
		bodyReader = bytes.NewReader(jsonData)
	}

	url := c.config.BaseURL + path
	req, err := http.NewRequest(method, url, bodyReader)
	if err != nil {
		return nil, err
	}

	if params != nil {
		q := req.URL.Query()
		for k, v := range params {
			q.Add(k, v)
		}
		req.URL.RawQuery = q.Encode()
	}

	req.Header.Set("Authorization", "Bearer "+c.config.APIKey)
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-SDK-Client", "go-sdk-v1")

	return c.httpClient.Do(req)
}
