package namaskah

import "encoding/json"

// VerifyService handles verification related tasks
type VerifyService struct {
	client *Client
}

// Verification represents a verification request/response
type Verification struct {
	ID          string  `json:"id"`
	Service     string  `json:"service"`
	Country     string  `json:"country"`
	PhoneNumber string  `json:"phone_number"`
	Cost        float64 `json:"cost,omitempty"`
	Status      string  `json:"status"`
	SMSCode     string  `json:"sms_code,omitempty"`
	SMSText     string  `json:"sms_text,omitempty"`
}

type CreateVerificationRequest struct {
	Service string `json:"service"`
	Country string `json:"country"`
}

func (s *VerifyService) Create(req CreateVerificationRequest) (*Verification, error) {
	resp, err := s.client.doRequest("POST", "/verify", req, nil)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var result Verification
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return &result, nil
}

func (s *VerifyService) Get(id string) (*Verification, error) {
	resp, err := s.client.doRequest("GET", "/verify/"+id, nil, nil)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var result Verification
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return &result, nil
}

func (s *VerifyService) Cancel(id string) error {
	resp, err := s.client.doRequest("POST", "/verify/"+id+"/cancel", nil, nil)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	return nil
}

func (s *VerifyService) GetCountries() (interface{}, error) {
	resp, err := s.client.doRequest("GET", "/countries", nil, nil)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var result interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return result, nil
}
