#!/bin/bash

set -e

echo "🚀 Starting Namaskah Monitoring Stack..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Navigate to monitoring directory
cd "$(dirname "$0")"

# Create required directories
mkdir -p grafana/provisioning/dashboards
mkdir -p grafana/provisioning/datasources

# Create Grafana datasource provisioning
cat > grafana/provisioning/datasources/prometheus.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF

# Create Grafana dashboard provisioning
cat > grafana/provisioning/dashboards/dashboards.yml << 'EOF'
apiVersion: 1

providers:
  - name: 'Namaskah Dashboards'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
EOF

# Start the monitoring stack
docker-compose -f docker-compose.yml up -d

echo "✅ Monitoring stack started!"
echo ""
echo "📊 Access points:"
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana: http://localhost:3000 (admin/admin123)"
echo "  - AlertManager: http://localhost:9093"
echo "  - cAdvisor: http://localhost:8080"
echo ""
echo "📈 Metrics endpoint: http://localhost:8000/metrics"
