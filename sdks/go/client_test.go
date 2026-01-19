package namaskah

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestNewClient(t *testing.T) {
	config := Config{
		APIKey: "test-key",
	}
	client := NewClient(config)

	if client.config.APIKey != "test-key" {
		t.Errorf("expected API key 'test-key', got %s", client.config.APIKey)
	}
	if client.config.BaseURL != "https://api.namaskah.com/api" {
		t.Errorf("expected default BaseURL, got %s", client.config.BaseURL)
	}
	if client.config.Timeout != 10*time.Second {
		t.Errorf("expected default timeout 10s, got %v", client.config.Timeout)
	}
}

// Redefining setup to allow handler injection
func setupMockServer(t *testing.T, method, path string, respBody interface{}, statusCode int) (*httptest.Server, *Client) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != method {
			t.Errorf("Expected method %s, got %s", method, r.Method)
		}
		if r.URL.Path != path {
			t.Errorf("Expected path %s, got %s", path, r.URL.Path)
		}
		if r.Header.Get("Authorization") != "Bearer test-key" {
			t.Errorf("Expected Authorization header")
		}

		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(statusCode)
		json.NewEncoder(w).Encode(respBody)
	}))

	config := Config{
		APIKey:  "test-key",
		BaseURL: server.URL,
	}
	client := NewClient(config)

	return server, client
}

func TestVerifyService_Create(t *testing.T) {
	mockResp := Verification{
		ID:      "v1",
		Service: "whatsapp",
		Country: "US",
		Status:  "pending",
	}

	server, client := setupMockServer(t, "POST", "/verify", mockResp, http.StatusOK)
	defer server.Close()

	req := CreateVerificationRequest{Service: "whatsapp", Country: "US"}
	verif, err := client.Verify.Create(req)

	if err != nil {
		t.Fatalf("Unexpected error: %v", err)
	}
	if verif.ID != "v1" {
		t.Errorf("Expected ID v1, got %s", verif.ID)
	}
}

func TestUsersService_GetProfile(t *testing.T) {
	mockResp := UserProfile{
		ID:    "u1",
		Email: "test@test.com",
	}

	server, client := setupMockServer(t, "GET", "/user/profile", mockResp, http.StatusOK)
	defer server.Close()

	profile, err := client.Users.GetProfile()
	if err != nil {
		t.Fatalf("Unexpected error: %v", err)
	}
	if profile.Email != "test@test.com" {
		t.Errorf("Expected email test@test.com, got %s", profile.Email)
	}
}

func TestReferralsService_GetStats(t *testing.T) {
	mockResp := ReferralStats{
		TotalReferrals: 5,
		TotalEarnings:  100.5,
	}

	server, client := setupMockServer(t, "GET", "/referrals/stats", mockResp, http.StatusOK)
	defer server.Close()

	stats, err := client.Referrals.GetStats()
	if err != nil {
		t.Fatalf("Unexpected error: %v", err)
	}
	if stats.TotalReferrals != 5 {
		t.Errorf("Expected 5 referrals, got %d", stats.TotalReferrals)
	}
}
