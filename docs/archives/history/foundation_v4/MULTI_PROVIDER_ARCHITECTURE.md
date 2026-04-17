# Multi-Provider Routing — Architecture Diagrams

Diagrams for the smart multi-provider routing system.
Implementation details -> docs/tasks/SMART_MULTI_PROVIDER_ROUTING.md

---

## System Architecture

```mermaid
graph TB
    subgraph "Request"
        REQ[User Request]
    end

    subgraph "Router"
        PR[ProviderRouter]
        COUNTRY{Country == US?}
        ENTERPRISE{prefer_enterprise?}
        TV_EN{TELNYX_ENABLED?}
        FS_EN{FIVESIM_ENABLED?}
    end

    subgraph "Adapters"
        TVA[TextVerifiedAdapter]
        TA[TelnyxAdapter]
        FSA[FiveSimAdapter]
    end

    subgraph "External APIs"
        TV[TextVerified API]
        TL[Telnyx API]
        FS[5sim API]
    end

    REQ --> PR
    PR --> COUNTRY
    COUNTRY -->|Yes| TVA
    COUNTRY -->|No| ENTERPRISE
    ENTERPRISE -->|Yes| TV_EN
    TV_EN -->|Yes| TA
    TV_EN -->|No| FS_EN
    ENTERPRISE -->|No| FS_EN
    FS_EN -->|Yes| FSA
    FS_EN -->|No| TA

    TVA --> TV
    TA --> TL
    FSA --> FS

    style PR fill:#4CAF50
    style TVA fill:#2196F3
    style TA fill:#FF9800
    style FSA fill:#9C27B0
```

---

## Purchase Flow

```mermaid
sequenceDiagram
    participant Client
    participant PurchaseEndpoint
    participant ProviderRouter
    participant Adapter
    participant ProviderAPI
    participant Database

    Client->>PurchaseEndpoint: POST /api/verification/request
    PurchaseEndpoint->>PurchaseEndpoint: Check balance, tier, idempotency
    PurchaseEndpoint->>ProviderRouter: purchase_with_failover(service, country, ...)
    ProviderRouter->>ProviderRouter: get_provider(country)
    ProviderRouter->>Adapter: purchase_number(service, country, ...)
    Adapter->>ProviderAPI: Buy number
    ProviderAPI-->>Adapter: Phone number + order ID
    Adapter-->>ProviderRouter: PurchaseResult
    ProviderRouter-->>PurchaseEndpoint: PurchaseResult
    PurchaseEndpoint->>Database: Save verification (provider, activation_id, cost)
    PurchaseEndpoint->>Database: Deduct user balance
    PurchaseEndpoint-->>Client: { phone_number, verification_id, cost }
```

---

## Failover Flow

```mermaid
sequenceDiagram
    participant Router as ProviderRouter
    participant Primary
    participant Secondary

    Router->>Primary: purchase_number()
    Primary-->>Router: RuntimeError (network timeout)

    Router->>Router: Is this a business error?
    Note over Router: "no inventory" -> raise immediately
    Note over Router: "insufficient balance" -> raise immediately

    Router->>Router: Is failover enabled?
    Router->>Secondary: purchase_number()
    Secondary-->>Router: PurchaseResult (success)
    Note over Router: routing_reason = "failover from Primary to Secondary"
```

---

## Polling Dispatch

```mermaid
flowchart TD
    START[Verification pending] --> READ[Read verification.provider from DB]
    READ --> WHICH{Which provider?}

    WHICH -->|textverified| TV[_poll_textverified\nsms.incoming with TV object]
    WHICH -->|telnyx| TL[_poll_telnyx\n5s loop, check_messages]
    WHICH -->|5sim| FS[_poll_fivesim\n5s loop, check_messages]
    WHICH -->|unknown| TO[_handle_timeout]

    TV -->|SMS received| DONE[Mark completed, notify user]
    TL -->|SMS received| DONE
    FS -->|SMS received| DONE

    TV -->|Timeout| REFUND[_handle_timeout]
    TL -->|Timeout| REFUND
    FS -->|Timeout| REFUND

    REFUND --> WHICH2{Which provider?}
    WHICH2 -->|textverified| R1[report_verification -> TV refunds]
    WHICH2 -->|telnyx| R2[report_failed -> cancel order]
    WHICH2 -->|5sim| R3[report_failed -> cancel activation]

    R1 -->|fails| FALLBACK[AutoRefundService platform refund]
    R2 -->|fails| FALLBACK
    R3 -->|fails| FALLBACK
```

---

## Provider Selection Logic

```mermaid
flowchart TD
    A[Request arrives] --> B{country == US?}
    B -->|Yes| TV[TextVerified]
    B -->|No| C{prefer_enterprise?}
    C -->|Yes| D{TELNYX_ENABLED?}
    D -->|Yes| TL[Telnyx]
    D -->|No| E{FIVESIM_ENABLED?}
    C -->|No| E
    E -->|Yes| FS[5sim]
    E -->|No| F{TELNYX_ENABLED?}
    F -->|Yes| TL
    F -->|No| TV[TextVerified fallback]
```

---

## HTTP Client Lifecycle

```mermaid
sequenceDiagram
    participant Router as ProviderRouter
    participant Adapter
    participant Client as httpx.AsyncClient

    Note over Router: First request
    Router->>Adapter: purchase_number()
    Adapter->>Adapter: _get_client()
    Adapter->>Client: Create new AsyncClient (once)
    Client-->>Adapter: client instance

    Note over Router: Second request (same adapter)
    Router->>Adapter: purchase_number()
    Adapter->>Adapter: _get_client()
    Note over Adapter: client already exists, reuse it
    Adapter->>Client: Reuse existing client

    Note over Router: App shutdown
    Router->>Adapter: __aexit__()
    Adapter->>Client: aclose()
```

---

## Balance Monitoring (Outstanding — Phase 4)

```mermaid
flowchart LR
    CRON[Every 5 minutes] --> CHECK[check_all_balances]
    CHECK --> TV[TextVerified balance]
    CHECK --> TL[Telnyx balance]
    CHECK --> FS[5sim balance]

    TV --> EVAL{Threshold?}
    TL --> EVAL
    FS --> EVAL

    EVAL -->|> $50| OK[Log OK]
    EVAL -->|$25-$50| WARN[Alert admin - warning]
    EVAL -->|$10-$25| CRIT[Alert admin - critical]
    EVAL -->|< $10| DISABLE[Auto-disable provider]
```
