package namaskah

import "encoding/json"

// UsersService handles user related tasks
type UsersService struct {
	client *Client
}

type UserProfile struct {
	ID    string `json:"id"`
	Email string `json:"email"`
}

type Balance struct {
	Balance  float64 `json:"balance"`
	Currency string  `json:"currency"`
}

func (s *UsersService) GetProfile() (*UserProfile, error) {
	resp, err := s.client.doRequest("GET", "/user/profile", nil, nil)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var result UserProfile
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return &result, nil
}

func (s *UsersService) GetBalance() (*Balance, error) {
	resp, err := s.client.doRequest("GET", "/billing/balance", nil, nil)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var result Balance
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return &result, nil
}
