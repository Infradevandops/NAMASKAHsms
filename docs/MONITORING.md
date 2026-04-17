# Monitoring Stack - Prometheus + Grafana

## Quick Start

```bash
cd monitoring
chmod +x start_monitoring.sh
./start_monitoring.sh
```

## Components

| Service | Port | Purpose |
|---------|------|---------|
| Prometheus | 9090 | Metrics collection & storage |
| Grafana | 3000 | Visualization & dashboards |
| AlertManager | 9093 | Alert routing & handling |
| cAdvisor | 8080 | Container metrics |
| Node Exporter | 9100 | System metrics |
| Redis Exporter | 9121 | Redis metrics |
| Postgres Exporter | 9187 | PostgreSQL metrics |
| NGINX Exporter | 9113 | NGINX metrics |

## Access

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin123)
- **AlertManager**: http://localhost:9093
- **API Metrics**: http://localhost:8000/metrics

## Metrics Collected

### FastAPI Application
- `http_requests_total` - Total HTTP requests by method, endpoint, status
- `http_request_duration_seconds` - Request latency histogram

### Infrastructure
- Container memory/CPU usage
- System metrics (disk, network, processes)
- Database connections & queries
- Redis operations

## Alerts

Critical alerts trigger when:
- Error rate > 5% for 5 minutes
- P95 latency > 1 second for 5 minutes
- Memory usage > 90% for 5 minutes
- Services are down

## Configuration Files

- `prometheus.yml` - Scrape targets & intervals
- `alert_rules.yml` - Alert definitions
- `alertmanager.yml` - Alert routing
- `docker-compose.yml` - Service definitions

## Stopping

```bash
docker-compose -f monitoring/docker-compose.yml down
```

## Data Retention

- Prometheus: 15 days
- Grafana: Persistent volume
- AlertManager: Persistent volume
