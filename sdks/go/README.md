# Namaskah Go SDK

Official Go library for Namaskah SMS Verification API.

## Installation

```bash
go get github.com/namaskah/namaskah-go
```

## Usage

```go
package main

import (
    "fmt"
    "github.com/namaskah/namaskah-go"
)

func main() {
    client := namaskah.NewClient(namaskah.Config{
        APIKey: "your_api_key_here",
    })

    countries, err := client.Verify.GetCountries()
    if err != nil {
        panic(err)
    }

    fmt.Printf("Available countries: %v\n", countries)
}
```

## Features

- **SMS Verification**: Request numbers, receive codes, and manage verification orders.
- **Forwarding**: Configure email and webhook forwarding for received SMS.
- **Analytics**: Retrieve your usage statistics and performance metrics.
- **Blacklist**: Manage your personal blacklist of phone numbers.

## License

MIT
