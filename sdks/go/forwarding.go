package namaskah

import "encoding/json"

// ForwardingService handles forwarding configuration
type ForwardingService struct {
	client *Client
}

type ForwardingConfig struct {
	EmailEnabled   bool   `json:"email_enabled"`
	EmailAddress   string `json:"email_address"`
	WebhookEnabled bool   `json:"webhook_enabled"`
	WebhookURL     string `json:"webhook_url"`
	WebhookSecret  string `json:"webhook_secret"`
	ForwardAll     bool   `json:"forward_all"`
}

func (s *ForwardingService) GetConfig() (*ForwardingConfig, error) {
	resp, err := s.client.doRequest("GET", "/forwarding", nil, nil)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var result struct {
		Config ForwardingConfig `json:"config"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return &result.Config, nil
}
