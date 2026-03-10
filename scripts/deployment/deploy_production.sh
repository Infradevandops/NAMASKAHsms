#!/bin/bash
# Production Deployment Script for Namaskah SMS
# Handles validation, deployment, and rollback

set -e

# Configuration
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.production"
BACKUP_DIR="./backups"
DEPLOY_LOG="./deploy.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$DEPLOY_LOG"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$DEPLOY_LOG"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$DEPLOY_LOG"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $1" | tee -a "$DEPLOY_LOG"
}

# Pre-deployment validation
validate_environment() {
    log "🔍 Validating deployment environment..."
    
    # Check required files
    local required_files=("$COMPOSE_FILE" "$ENV_FILE" "Dockerfile" "requirements.txt")
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            error "Required file missing: $file"
            exit 1
        fi
    done
    
    # Validate configuration
    if ! python scripts/validate_config.py --env-file "$ENV_FILE"; then
        error "Configuration validation failed"
        exit 1
    fi
    
    # Check Docker and Docker Compose
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check available disk space (minimum 5GB)
    local available_space=$(df . | awk 'NR==2 {print $4}')
    if [[ $available_space -lt 5242880 ]]; then  # 5GB in KB
        warn "Low disk space available: $(($available_space / 1024 / 1024))GB"
    fi
    
    log "✅ Environment validation completed"
}

# Database backup
backup_database() {
    log "💾 Creating database backup..."
    
    mkdir -p "$BACKUP_DIR"
    local backup_file="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"
    
    # Check if database is running
    if docker-compose -f "$COMPOSE_FILE" ps db | grep -q "Up"; then
        docker-compose -f "$COMPOSE_FILE" exec -T db pg_dump -U namaskah_user namaskah_prod > "$backup_file"
        
        if [[ -f "$backup_file" && -s "$backup_file" ]]; then
            log "✅ Database backup created: $backup_file"
            echo "$backup_file" > "$BACKUP_DIR/latest_backup.txt"
        else
            error "Database backup failed"
            exit 1
        fi
    else
        warn "Database not running, skipping backup"
    fi
}

# Build and deploy
deploy_application() {
    log "🚀 Starting production deployment..."
    
    # Pull latest images
    log "📥 Pulling base images..."
    docker-compose -f "$COMPOSE_FILE" pull --ignore-pull-failures
    
    # Build application image
    log "🔨 Building application image..."
    docker-compose -f "$COMPOSE_FILE" build --no-cache
    
    # Start services with rolling update
    log "🔄 Starting services..."
    
    # Start infrastructure services first
    docker-compose -f "$COMPOSE_FILE" up -d db redis
    
    # Wait for infrastructure to be ready
    log "⏳ Waiting for infrastructure services..."
    sleep 30
    
    # Check infrastructure health
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if docker-compose -f "$COMPOSE_FILE" exec -T db pg_isready -U namaskah_user -d namaskah_prod &>/dev/null && \
           docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping &>/dev/null; then
            log "✅ Infrastructure services are ready"
            break
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            error "Infrastructure services failed to start"
            exit 1
        fi
        
        info "Waiting for infrastructure... (attempt $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    # Start application services
    log "🚀 Starting application services..."
    docker-compose -f "$COMPOSE_FILE" up -d app1 app2 app3
    
    # Start load balancer
    log "⚖️ Starting load balancer..."
    docker-compose -f "$COMPOSE_FILE" up -d nginx
    
    log "✅ Deployment completed"
}

# Health check validation
validate_deployment() {
    log "🏥 Validating deployment health..."
    
    local max_attempts=60
    local attempt=1
    local health_url="http://localhost/system/health"
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s "$health_url" &>/dev/null; then
            log "✅ Application is responding to health checks"
            
            # Get detailed health status
            local health_response=$(curl -s "$health_url")
            info "Health check response: $health_response"
            
            return 0
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            error "Application failed health checks"
            return 1
        fi
        
        info "Waiting for application... (attempt $attempt/$max_attempts)"
        sleep 5
        ((attempt++))
    done
}

# Performance validation
validate_performance() {
    log "⚡ Running performance validation..."
    
    # Simple load test
    if command -v ab &> /dev/null; then
        log "Running Apache Bench test..."
        ab -n 100 -c 10 http://localhost/system/health > /tmp/ab_results.txt 2>&1
        
        local requests_per_second=$(grep "Requests per second" /tmp/ab_results.txt | awk '{print $4}')
        local response_time=$(grep "Time per request" /tmp/ab_results.txt | head -1 | awk '{print $4}')
        
        info "Performance results: ${requests_per_second} req/sec, ${response_time}ms avg response time"
        
        # Check if performance is acceptable
        if (( $(echo "$requests_per_second > 50" | bc -l) )); then
            log "✅ Performance validation passed"
        else
            warn "Performance may be suboptimal: ${requests_per_second} req/sec"
        fi
    else
        warn "Apache Bench not available, skipping performance test"
    fi
}

# Rollback function
rollback_deployment() {
    error "🔄 Rolling back deployment..."
    
    # Stop current services
    docker-compose -f "$COMPOSE_FILE" down
    
    # Restore from backup if available
    if [[ -f "$BACKUP_DIR/latest_backup.txt" ]]; then
        local backup_file=$(cat "$BACKUP_DIR/latest_backup.txt")
        if [[ -f "$backup_file" ]]; then
            log "📥 Restoring database from backup: $backup_file"
            
            # Start only database for restore
            docker-compose -f "$COMPOSE_FILE" up -d db
            sleep 30
            
            # Restore database
            docker-compose -f "$COMPOSE_FILE" exec -T db psql -U namaskah_user -d namaskah_prod < "$backup_file"
            
            log "✅ Database restored from backup"
        fi
    fi
    
    error "❌ Rollback completed. Please investigate the issues."
    exit 1
}

# Cleanup old resources
cleanup_resources() {
    log "🧹 Cleaning up old resources..."
    
    # Remove unused images
    docker image prune -f
    
    # Remove old backups (keep last 7 days)
    find "$BACKUP_DIR" -name "backup_*.sql" -mtime +7 -delete
    
    log "✅ Cleanup completed"
}

# Show deployment status
show_status() {
    log "📊 Deployment Status:"
    echo ""
    docker-compose -f "$COMPOSE_FILE" ps
    echo ""
    
    log "📈 Resource Usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
    echo ""
    
    log "📋 Service Logs (last 10 lines):"
    docker-compose -f "$COMPOSE_FILE" logs --tail=10
}

# Main deployment function
main() {
    local command="${1:-deploy}"
    
    case "$command" in
        "validate")
            validate_environment
            ;;
        "backup")
            backup_database
            ;;
        "deploy")
            validate_environment
            backup_database
            deploy_application
            
            if validate_deployment && validate_performance; then
                cleanup_resources
                show_status
                log "🎉 Production deployment successful!"
            else
                rollback_deployment
            fi
            ;;
        "rollback")
            rollback_deployment
            ;;
        "status")
            show_status
            ;;
        "cleanup")
            cleanup_resources
            ;;
        *)
            echo "Usage: $0 {validate|backup|deploy|rollback|status|cleanup}"
            echo ""
            echo "Commands:"
            echo "  validate  - Validate environment and configuration"
            echo "  backup    - Create database backup"
            echo "  deploy    - Full production deployment"
            echo "  rollback  - Rollback to previous version"
            echo "  status    - Show deployment status"
            echo "  cleanup   - Clean up old resources"
            exit 1
            ;;
    esac
}

# Trap errors and rollback
trap 'error "Deployment failed at line $LINENO"; rollback_deployment' ERR

main "$@"