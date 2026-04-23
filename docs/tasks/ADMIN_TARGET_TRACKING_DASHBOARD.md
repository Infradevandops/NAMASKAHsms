# Admin Portal - Monthly User Target Tracking Dashboard

**Version**: 1.0.0  
**Status**: Planning  
**Priority**: HIGH  
**Effort**: 2 days  
**Created**: March 2026  
**Target**: Month 6 Break-Even Goal

---

## Executive Summary

Create an admin dashboard widget to track progress toward the 350 monthly user target (break-even point). Display current users, remaining users needed, percentage complete, and whether target is met.

**Current State**: No visibility into monthly user acquisition targets  
**Target State**: Real-time dashboard showing progress toward 350 user break-even goal  
**Business Impact**: Track break-even progress, adjust marketing spend, monitor growth velocity

---

## Requirements

### Functional Requirements

#### FR1: Monthly Target Dashboard Widget
- Display target: 350 users (break-even point)
- Display current total users
- Display remaining users needed
- Display percentage complete
- Display status: "On Track" / "Behind" / "Target Met"
- Display user breakdown by tier (Freemium, PAYG, Pro, Custom)
- Display expected vs actual tier mix

#### FR2: Progress Visualization
- Progress bar showing completion percentage
- Color coding:
  - Red: 0-50% (Behind)
  - Yellow: 51-80% (On Track)
  - Green: 81-100% (Target Met)
- Daily acquisition rate (users per day)
- Days remaining to target (if not met)
- Projected completion date

#### FR3: Financial Impact Display
- Current monthly revenue
- Target monthly revenue at 350 users: $3,630 to $4,500
- Revenue gap
- Break-even status: "Profitable" / "Break-even" / "Investment Phase"

#### FR4: Inventory Status
- API provider balance (TextVerified, Telnyx, 5sim)
- Alert if balance below $20 per provider
- Monthly API spend vs budget ($450-$1,250)
- Infrastructure cost (current droplet size)

---

## Database Requirements

### New Table: monthly_targets

```sql
CREATE TABLE monthly_targets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    target_month VARCHAR(7) NOT NULL, -- Format: YYYY-MM
    target_users INTEGER NOT NULL DEFAULT 350,
    target_revenue DECIMAL(10, 2) NOT NULL DEFAULT 4000.00,
    target_freemium_pct DECIMAL(5, 2) DEFAULT 40.00,
    target_payg_pct DECIMAL(5, 2) DEFAULT 30.00,
    target_pro_pct DECIMAL(5, 2) DEFAULT 25.00,
    target_custom_pct DECIMAL(5, 2) DEFAULT 5.00,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_monthly_targets_month ON monthly_targets(target_month);
CREATE INDEX idx_monthly_targets_active ON monthly_targets(is_active);
```

### New Table: daily_user_snapshots

```sql
CREATE TABLE daily_user_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot_date DATE NOT NULL,
    total_users INTEGER NOT NULL,
    freemium_users INTEGER NOT NULL,
    payg_users INTEGER NOT NULL,
    pro_users INTEGER NOT NULL,
    custom_users INTEGER NOT NULL,
    new_users_today INTEGER NOT NULL,
    churned_users_today INTEGER DEFAULT 0,
    daily_revenue DECIMAL(10, 2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_daily_snapshots_date ON daily_user_snapshots(snapshot_date);
CREATE INDEX idx_daily_snapshots_created ON daily_user_snapshots(created_at DESC);
```

---

## Backend Implementation

### Task 1: Create Target Tracking Service

**File**: `app/services/target_tracking_service.py`

```python
from datetime import datetime, date
from sqlalchemy.orm import Session
from app.models.user import User

class TargetTrackingService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_current_month_target(self):
        """Get active target for current month"""
        current_month = datetime.now().strftime("%Y-%m")
        target = self.db.query(MonthlyTarget).filter(
            MonthlyTarget.target_month == current_month,
            MonthlyTarget.is_active == True
        ).first()
        
        if not target:
            # Create default target
            target = MonthlyTarget(
                target_month=current_month,
                target_users=350,
                target_revenue=4000.00
            )
            self.db.add(target)
            self.db.commit()
        
        return target
    
    def get_current_user_stats(self):
        """Get current user counts by tier"""
        total = self.db.query(User).filter(User.is_active == True).count()
        freemium = self.db.query(User).filter(
            User.subscription_tier == "freemium",
            User.is_active == True
        ).count()
        payg = self.db.query(User).filter(
            User.subscription_tier == "payg",
            User.is_active == True
        ).count()
        pro = self.db.query(User).filter(
            User.subscription_tier == "pro",
            User.is_active == True
        ).count()
        custom = self.db.query(User).filter(
            User.subscription_tier == "custom",
            User.is_active == True
        ).count()
        
        return {
            "total": total,
            "freemium": freemium,
            "payg": payg,
            "pro": pro,
            "custom": custom
        }
    
    def calculate_progress(self):
        """Calculate progress toward monthly target"""
        target = self.get_current_month_target()
        stats = self.get_current_user_stats()
        
        remaining = target.target_users - stats["total"]
        percentage = (stats["total"] / target.target_users) * 100
        
        # Calculate status
        if percentage >= 100:
            status = "Target Met"
            color = "green"
        elif percentage >= 80:
            status = "On Track"
            color = "green"
        elif percentage >= 50:
            status = "On Track"
            color = "yellow"
        else:
            status = "Behind"
            color = "red"
        
        # Calculate daily acquisition rate
        days_in_month = datetime.now().day
        daily_rate = stats["total"] / days_in_month if days_in_month > 0 else 0
        
        # Calculate days remaining
        days_left_in_month = (datetime.now().replace(day=1, month=datetime.now().month+1) - datetime.now()).days
        
        # Projected completion
        if daily_rate > 0:
            days_to_target = remaining / daily_rate
            projected_date = datetime.now() + timedelta(days=days_to_target)
        else:
            projected_date = None
        
        return {
            "target": target.target_users,
            "current": stats["total"],
            "remaining": remaining,
            "percentage": round(percentage, 1),
            "status": status,
            "color": color,
            "daily_rate": round(daily_rate, 1),
            "days_left": days_left_in_month,
            "projected_date": projected_date.strftime("%Y-%m-%d") if projected_date else None,
            "breakdown": stats
        }
    
    def calculate_revenue_status(self):
        """Calculate current revenue vs target"""
        from app.models.transaction import Transaction
        
        # Get current month revenue
        start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0)
        revenue = self.db.query(func.sum(Transaction.amount)).filter(
            Transaction.type == "credit",
            Transaction.created_at >= start_of_month
        ).scalar() or 0
        
        target = self.get_current_month_target()
        gap = target.target_revenue - revenue
        
        if revenue >= target.target_revenue:
            status = "Profitable"
        elif revenue >= (target.target_revenue * 0.9):
            status = "Break-even"
        else:
            status = "Investment Phase"
        
        return {
            "current_revenue": float(revenue),
            "target_revenue": float(target.target_revenue),
            "gap": float(gap),
            "status": status
        }
    
    def get_api_inventory_status(self):
        """Get API provider balance status"""
        # This would integrate with actual provider APIs
        # For now, return mock data
        return {
            "textverified": {
                "balance": 45.00,
                "status": "OK",
                "alert": False
            },
            "telnyx": {
                "balance": 15.00,
                "status": "Low",
                "alert": True
            },
            "5sim": {
                "balance": 25.00,
                "status": "OK",
                "alert": False
            },
            "total_balance": 85.00,
            "monthly_spend": 320.00,
            "budget": 1250.00
        }
    
    def create_daily_snapshot(self):
        """Create daily user snapshot for tracking"""
        today = date.today()
        stats = self.get_current_user_stats()
        
        # Check if snapshot already exists
        existing = self.db.query(DailyUserSnapshot).filter(
            DailyUserSnapshot.snapshot_date == today
        ).first()
        
        if existing:
            return existing
        
        # Get yesterday's snapshot for comparison
        yesterday = today - timedelta(days=1)
        yesterday_snapshot = self.db.query(DailyUserSnapshot).filter(
            DailyUserSnapshot.snapshot_date == yesterday
        ).first()
        
        new_users = stats["total"] - (yesterday_snapshot.total_users if yesterday_snapshot else 0)
        
        snapshot = DailyUserSnapshot(
            snapshot_date=today,
            total_users=stats["total"],
            freemium_users=stats["freemium"],
            payg_users=stats["payg"],
            pro_users=stats["pro"],
            custom_users=stats["custom"],
            new_users_today=new_users
        )
        
        self.db.add(snapshot)
        self.db.commit()
        
        return snapshot
```

---

### Task 2: Create Admin API Endpoints

**File**: `app/api/admin/target_tracking.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, require_admin
from app.services.target_tracking_service import TargetTrackingService

router = APIRouter(prefix="/api/v1/admin/targets", tags=["Admin Targets"])

@router.get("/progress")
async def get_target_progress(
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get current progress toward monthly user target"""
    service = TargetTrackingService(db)
    return service.calculate_progress()

@router.get("/revenue")
async def get_revenue_status(
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get current revenue vs target"""
    service = TargetTrackingService(db)
    return service.calculate_revenue_status()

@router.get("/inventory")
async def get_inventory_status(
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get API provider inventory status"""
    service = TargetTrackingService(db)
    return service.get_api_inventory_status()

@router.get("/dashboard")
async def get_full_dashboard(
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get complete dashboard data"""
    service = TargetTrackingService(db)
    
    return {
        "progress": service.calculate_progress(),
        "revenue": service.calculate_revenue_status(),
        "inventory": service.get_api_inventory_status()
    }

@router.post("/snapshot")
async def create_daily_snapshot(
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create daily user snapshot"""
    service = TargetTrackingService(db)
    snapshot = service.create_daily_snapshot()
    return {"message": "Snapshot created", "snapshot_date": str(snapshot.snapshot_date)}
```

---

## Frontend Implementation

### Task 3: Create Target Dashboard Widget

**File**: `static/admin/components/target-dashboard.js`

```javascript
class TargetDashboard {
    constructor() {
        this.container = document.getElementById('target-dashboard');
        this.refreshInterval = 60000; // 1 minute
    }
    
    async init() {
        await this.loadData();
        this.startAutoRefresh();
    }
    
    async loadData() {
        try {
            const response = await fetch('/api/v1/admin/targets/dashboard', {
                headers: { 'Authorization': `Bearer ${getToken()}` }
            });
            const data = await response.json();
            this.render(data);
        } catch (error) {
            console.error('Failed to load target dashboard:', error);
            this.renderError();
        }
    }
    
    render(data) {
        const { progress, revenue, inventory } = data;
        
        const html = `
            <div class="target-dashboard-grid">
                <!-- User Target Progress -->
                <div class="dashboard-card">
                    <h3>Monthly User Target</h3>
                    <div class="target-stats">
                        <div class="stat-large">
                            <span class="stat-value">${progress.current}</span>
                            <span class="stat-label">/ ${progress.target} users</span>
                        </div>
                        <div class="progress-bar-container">
                            <div class="progress-bar" style="width: ${progress.percentage}%; background-color: ${this.getProgressColor(progress.color)}"></div>
                        </div>
                        <div class="progress-info">
                            <span class="badge badge-${progress.color}">${progress.status}</span>
                            <span>${progress.percentage}% Complete</span>
                        </div>
                    </div>
                    
                    <div class="target-details">
                        <div class="detail-row">
                            <span>Remaining:</span>
                            <strong>${progress.remaining} users</strong>
                        </div>
                        <div class="detail-row">
                            <span>Daily Rate:</span>
                            <strong>${progress.daily_rate} users/day</strong>
                        </div>
                        <div class="detail-row">
                            <span>Days Left:</span>
                            <strong>${progress.days_left} days</strong>
                        </div>
                        ${progress.projected_date ? `
                        <div class="detail-row">
                            <span>Projected:</span>
                            <strong>${progress.projected_date}</strong>
                        </div>
                        ` : ''}
                    </div>
                    
                    <div class="tier-breakdown">
                        <h4>User Mix</h4>
                        <div class="tier-grid">
                            <div class="tier-item">
                                <span class="tier-label">Freemium</span>
                                <span class="tier-value">${progress.breakdown.freemium}</span>
                                <span class="tier-pct">${this.calculatePct(progress.breakdown.freemium, progress.current)}%</span>
                            </div>
                            <div class="tier-item">
                                <span class="tier-label">PAYG</span>
                                <span class="tier-value">${progress.breakdown.payg}</span>
                                <span class="tier-pct">${this.calculatePct(progress.breakdown.payg, progress.current)}%</span>
                            </div>
                            <div class="tier-item">
                                <span class="tier-label">Pro</span>
                                <span class="tier-value">${progress.breakdown.pro}</span>
                                <span class="tier-pct">${this.calculatePct(progress.breakdown.pro, progress.current)}%</span>
                            </div>
                            <div class="tier-item">
                                <span class="tier-label">Custom</span>
                                <span class="tier-value">${progress.breakdown.custom}</span>
                                <span class="tier-pct">${this.calculatePct(progress.breakdown.custom, progress.current)}%</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Revenue Status -->
                <div class="dashboard-card">
                    <h3>Revenue Status</h3>
                    <div class="revenue-stats">
                        <div class="stat-row">
                            <span>Current Revenue:</span>
                            <strong class="text-primary">$${revenue.current_revenue.toFixed(2)}</strong>
                        </div>
                        <div class="stat-row">
                            <span>Target Revenue:</span>
                            <strong>$${revenue.target_revenue.toFixed(2)}</strong>
                        </div>
                        <div class="stat-row">
                            <span>Gap:</span>
                            <strong class="${revenue.gap > 0 ? 'text-danger' : 'text-success'}">
                                $${Math.abs(revenue.gap).toFixed(2)}
                            </strong>
                        </div>
                        <div class="status-badge">
                            <span class="badge badge-${this.getRevenueColor(revenue.status)}">
                                ${revenue.status}
                            </span>
                        </div>
                    </div>
                </div>
                
                <!-- API Inventory -->
                <div class="dashboard-card">
                    <h3>API Inventory</h3>
                    <div class="inventory-grid">
                        ${Object.entries(inventory).filter(([key]) => key !== 'total_balance' && key !== 'monthly_spend' && key !== 'budget').map(([provider, data]) => `
                            <div class="inventory-item ${data.alert ? 'alert' : ''}">
                                <span class="provider-name">${provider}</span>
                                <span class="provider-balance">$${data.balance.toFixed(2)}</span>
                                <span class="badge badge-${data.status === 'OK' ? 'success' : 'warning'}">
                                    ${data.status}
                                </span>
                            </div>
                        `).join('')}
                    </div>
                    <div class="inventory-summary">
                        <div class="summary-row">
                            <span>Total Balance:</span>
                            <strong>$${inventory.total_balance.toFixed(2)}</strong>
                        </div>
                        <div class="summary-row">
                            <span>Monthly Spend:</span>
                            <strong>$${inventory.monthly_spend.toFixed(2)}</strong>
                        </div>
                        <div class="summary-row">
                            <span>Budget:</span>
                            <strong>$${inventory.budget.toFixed(2)}</strong>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        this.container.innerHTML = html;
    }
    
    calculatePct(value, total) {
        return total > 0 ? ((value / total) * 100).toFixed(1) : 0;
    }
    
    getProgressColor(color) {
        const colors = {
            'red': '#ef4444',
            'yellow': '#f59e0b',
            'green': '#10b981'
        };
        return colors[color] || '#6b7280';
    }
    
    getRevenueColor(status) {
        const colors = {
            'Profitable': 'success',
            'Break-even': 'warning',
            'Investment Phase': 'danger'
        };
        return colors[status] || 'secondary';
    }
    
    renderError() {
        this.container.innerHTML = `
            <div class="alert alert-danger">
                Failed to load target dashboard. Please refresh the page.
            </div>
        `;
    }
    
    startAutoRefresh() {
        setInterval(() => this.loadData(), this.refreshInterval);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    const dashboard = new TargetDashboard();
    dashboard.init();
});
```

---

### Task 4: Add to Admin Dashboard

**File**: `templates/admin/dashboard.html`

Add new section:

```html
<div class="dashboard-section">
    <div class="section-header">
        <h2>Monthly Target Progress</h2>
        <button onclick="targetDashboard.loadData()" class="btn-refresh">
            <i class="icon-refresh"></i> Refresh
        </button>
    </div>
    <div id="target-dashboard"></div>
</div>

<script src="/static/admin/components/target-dashboard.js"></script>
```

---

## Background Jobs

### Task 5: Daily Snapshot Job

**File**: `app/jobs/daily_snapshot_job.py`

```python
from apscheduler.schedulers.background import BackgroundScheduler
from app.services.target_tracking_service import TargetTrackingService
from app.core.database import get_db

def create_daily_snapshot():
    """Create daily user snapshot - runs at midnight"""
    db = next(get_db())
    try:
        service = TargetTrackingService(db)
        service.create_daily_snapshot()
        print(f"Daily snapshot created: {date.today()}")
    except Exception as e:
        print(f"Failed to create daily snapshot: {e}")
    finally:
        db.close()

# Schedule job
scheduler = BackgroundScheduler()
scheduler.add_job(create_daily_snapshot, 'cron', hour=0, minute=5)
scheduler.start()
```

---

## Testing

### Unit Tests

```python
def test_calculate_progress():
    service = TargetTrackingService(db)
    progress = service.calculate_progress()
    assert "target" in progress
    assert "current" in progress
    assert "remaining" in progress
    assert "percentage" in progress

def test_revenue_status():
    service = TargetTrackingService(db)
    revenue = service.calculate_revenue_status()
    assert "current_revenue" in revenue
    assert "target_revenue" in revenue
    assert "status" in revenue
```

---

## Deployment Checklist

- [ ] Run database migrations (monthly_targets, daily_user_snapshots)
- [ ] Deploy backend service and API endpoints
- [ ] Deploy frontend widget
- [ ] Set up daily snapshot cron job
- [ ] Test dashboard display
- [ ] Verify calculations
- [ ] Set initial target for current month

---

## Success Metrics

- Dashboard loads in < 2 seconds
- Auto-refresh every 60 seconds
- Accurate user counts
- Correct percentage calculations
- Real-time status updates

---

**Status**: Ready for Implementation  
**Estimated Effort**: 2 days  
**Priority**: HIGH (Critical for tracking break-even goal)
