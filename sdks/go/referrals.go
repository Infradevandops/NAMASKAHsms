package namaskah

import "encoding/json"

// ReferralsService handles referral related tasks
type ReferralsService struct {
	client *Client
}

type ReferralStats struct {
	TotalReferrals int     `json:"total_referrals"`
	TotalEarnings  float64 `json:"total_earnings"`
}

type Referral struct {
	ID        string `json:"id"`
	Status    string `json:"status"`
	CreatedAt string `json:"created_at"`
}

func (s *ReferralsService) GetStats() (*ReferralStats, error) {
	resp, err := s.client.doRequest("GET", "/referrals/stats", nil, nil)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var result ReferralStats
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return &result, nil
}

func (s *ReferralsService) List() ([]Referral, error) {
	resp, err := s.client.doRequest("GET", "/referrals/list", nil, nil)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var result []Referral
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return result, nil
}
