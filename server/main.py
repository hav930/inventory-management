from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
from mock_data import inventory_items, orders, demand_forecasts, backlog_items, spending_summary, monthly_spending, category_spending, recent_transactions, purchase_orders, submitted_restocking_orders

app = FastAPI(title="Factory Inventory Management System")

# Quarter mapping for date filtering
QUARTER_MAP = {
    'Q1-2025': ['2025-01', '2025-02', '2025-03'],
    'Q2-2025': ['2025-04', '2025-05', '2025-06'],
    'Q3-2025': ['2025-07', '2025-08', '2025-09'],
    'Q4-2025': ['2025-10', '2025-11', '2025-12']
}

# Supplier lead time per inventory category, in days. No per-item lead-time data exists
# in the JSON fixtures, so the Restocking tab derives it from category alone.
CATEGORY_LEAD_TIME_DAYS = {
    "Sensors": 7,
    "Controllers": 10,
    "Power Supplies": 14,
    "Circuit Boards": 21,
    "Actuators": 10,
}
DEFAULT_LEAD_TIME_DAYS = 14

def filter_by_month(items: list, month: Optional[str]) -> list:
    """Filter items by month/quarter based on order_date field"""
    if not month or month == 'all':
        return items

    if month.startswith('Q'):
        # Handle quarters
        if month in QUARTER_MAP:
            months = QUARTER_MAP[month]
            return [item for item in items if any(m in item.get('order_date', '') for m in months)]
    else:
        # Direct month match
        return [item for item in items if month in item.get('order_date', '')]

    return items

def apply_filters(items: list, warehouse: Optional[str] = None, category: Optional[str] = None,
                 status: Optional[str] = None) -> list:
    """Apply common filters to a list of items"""
    filtered = items

    if warehouse and warehouse != 'all':
        filtered = [item for item in filtered if item.get('warehouse') == warehouse]

    if category and category != 'all':
        filtered = [item for item in filtered if item.get('category', '').lower() == category.lower()]

    if status and status != 'all':
        filtered = [item for item in filtered if item.get('status', '').lower() == status.lower()]

    return filtered

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class InventoryItem(BaseModel):
    id: str
    sku: str
    name: str
    category: str
    warehouse: str
    quantity_on_hand: int
    reorder_point: int
    unit_cost: float
    location: str
    last_updated: str

class Order(BaseModel):
    id: str
    order_number: str
    customer: str
    items: List[dict]
    status: str
    order_date: str
    expected_delivery: str
    total_value: float
    actual_delivery: Optional[str] = None
    warehouse: Optional[str] = None
    category: Optional[str] = None

class DemandForecast(BaseModel):
    id: str
    item_sku: str
    item_name: str
    current_demand: int
    forecasted_demand: int
    trend: str
    period: str

class BacklogItem(BaseModel):
    id: str
    order_id: str
    item_sku: str
    item_name: str
    quantity_needed: int
    quantity_available: int
    days_delayed: int
    priority: str
    has_purchase_order: Optional[bool] = False

class PurchaseOrder(BaseModel):
    id: str
    backlog_item_id: str
    supplier_name: str
    quantity: int
    unit_cost: float
    expected_delivery_date: str
    status: str
    created_date: str
    notes: Optional[str] = None

class CreatePurchaseOrderRequest(BaseModel):
    backlog_item_id: str
    supplier_name: str
    quantity: int
    unit_cost: float
    expected_delivery_date: str
    notes: Optional[str] = None

class RestockingRecommendation(BaseModel):
    sku: str
    name: str
    category: str
    warehouse: str
    quantity_on_hand: int
    forecasted_demand: int
    shortage: int
    suggested_quantity: int
    unit_cost: float
    line_total: float
    lead_time_days: int

class RestockingOrderItem(BaseModel):
    sku: str
    name: str
    quantity: int
    unit_cost: float
    lead_time_days: int
    line_total: float

class CreateRestockingOrderRequest(BaseModel):
    budget: float
    items: List[RestockingOrderItem]

class SubmittedRestockingOrder(BaseModel):
    id: str
    order_number: str
    submitted_date: str
    expected_delivery: str
    total_value: float
    items: List[RestockingOrderItem]
    status: str

# API endpoints
@app.get("/")
def root():
    return {"message": "Factory Inventory Management System API", "version": "1.0.0"}

@app.get("/api/inventory", response_model=List[InventoryItem])
def get_inventory(
    warehouse: Optional[str] = None,
    category: Optional[str] = None
):
    """Get all inventory items with optional filtering"""
    return apply_filters(inventory_items, warehouse, category)

@app.get("/api/inventory/{item_id}", response_model=InventoryItem)
def get_inventory_item(item_id: str):
    """Get a specific inventory item"""
    item = next((item for item in inventory_items if item["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.get("/api/orders", response_model=List[Order])
def get_orders(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get all orders with optional filtering"""
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)
    return filtered_orders

@app.get("/api/orders/{order_id}", response_model=Order)
def get_order(order_id: str):
    """Get a specific order"""
    order = next((order for order in orders if order["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.get("/api/demand", response_model=List[DemandForecast])
def get_demand_forecasts():
    """Get demand forecasts"""
    return demand_forecasts

@app.get("/api/backlog", response_model=List[BacklogItem])
def get_backlog():
    """Get backlog items with purchase order status"""
    # Add has_purchase_order flag to each backlog item
    result = []
    for item in backlog_items:
        item_dict = dict(item)
        # Check if this backlog item has a purchase order
        has_po = any(po["backlog_item_id"] == item["id"] for po in purchase_orders)
        item_dict["has_purchase_order"] = has_po
        result.append(item_dict)
    return result

@app.get("/api/dashboard/summary")
def get_dashboard_summary(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get summary statistics for dashboard with optional filtering"""
    # Filter inventory
    filtered_inventory = apply_filters(inventory_items, warehouse, category)

    # Filter orders
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)

    total_inventory_value = sum(item["quantity_on_hand"] * item["unit_cost"] for item in filtered_inventory)
    low_stock_items = len([item for item in filtered_inventory if item["quantity_on_hand"] <= item["reorder_point"]])
    pending_orders = len([order for order in filtered_orders if order["status"] in ["Processing", "Backordered"]])
    total_backlog_items = len(backlog_items)

    return {
        "total_inventory_value": round(total_inventory_value, 2),
        "low_stock_items": low_stock_items,
        "pending_orders": pending_orders,
        "total_backlog_items": total_backlog_items,
        "total_orders_value": sum(order["total_value"] for order in filtered_orders)
    }

@app.get("/api/spending/summary")
def get_spending_summary():
    """Get spending summary statistics"""
    return spending_summary

@app.get("/api/spending/monthly")
def get_monthly_spending():
    """Get monthly spending breakdown"""
    return monthly_spending

@app.get("/api/spending/categories")
def get_category_spending():
    """Get spending by category"""
    return category_spending

@app.get("/api/spending/transactions")
def get_recent_transactions():
    """Get recent transactions"""
    return recent_transactions

@app.get("/api/reports/quarterly")
def get_quarterly_reports():
    """Get quarterly performance reports"""
    # Calculate quarterly statistics from orders
    quarters = {}

    for order in orders:
        order_date = order.get('order_date', '')
        # Determine quarter
        if '2025-01' in order_date or '2025-02' in order_date or '2025-03' in order_date:
            quarter = 'Q1-2025'
        elif '2025-04' in order_date or '2025-05' in order_date or '2025-06' in order_date:
            quarter = 'Q2-2025'
        elif '2025-07' in order_date or '2025-08' in order_date or '2025-09' in order_date:
            quarter = 'Q3-2025'
        elif '2025-10' in order_date or '2025-11' in order_date or '2025-12' in order_date:
            quarter = 'Q4-2025'
        else:
            continue

        if quarter not in quarters:
            quarters[quarter] = {
                'quarter': quarter,
                'total_orders': 0,
                'total_revenue': 0,
                'delivered_orders': 0,
                'avg_order_value': 0
            }

        quarters[quarter]['total_orders'] += 1
        quarters[quarter]['total_revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            quarters[quarter]['delivered_orders'] += 1

    # Calculate averages and fulfillment rate
    result = []
    for q, data in quarters.items():
        if data['total_orders'] > 0:
            data['avg_order_value'] = round(data['total_revenue'] / data['total_orders'], 2)
            data['fulfillment_rate'] = round((data['delivered_orders'] / data['total_orders']) * 100, 1)
        result.append(data)

    # Sort by quarter
    result.sort(key=lambda x: x['quarter'])
    return result

@app.get("/api/reports/monthly-trends")
def get_monthly_trends():
    """Get month-over-month trends"""
    months = {}

    for order in orders:
        order_date = order.get('order_date', '')
        if not order_date:
            continue

        # Extract month (format: YYYY-MM-DD)
        month = order_date[:7]  # Gets YYYY-MM

        if month not in months:
            months[month] = {
                'month': month,
                'order_count': 0,
                'revenue': 0,
                'delivered_count': 0
            }

        months[month]['order_count'] += 1
        months[month]['revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            months[month]['delivered_count'] += 1

    # Convert to list and sort
    result = list(months.values())
    result.sort(key=lambda x: x['month'])
    return result

def _lead_time_days_for(category: str) -> int:
    return CATEGORY_LEAD_TIME_DAYS.get(category, DEFAULT_LEAD_TIME_DAYS)


@app.get("/api/restocking/recommendations", response_model=List[RestockingRecommendation])
def get_restocking_recommendations(budget: float = 0.0):
    """Recommend items to restock within the given budget.

    Joins demand forecasts to inventory on SKU, computes shortage per item, ranks
    by shortage size, then greedily allocates spend. Partial fills are allowed so
    the last item can absorb whatever budget is left over instead of being skipped.
    """
    inventory_by_sku = {item["sku"]: item for item in inventory_items}

    # Build candidate list from forecasts that have a matching inventory record
    # AND a positive shortage. Items already over-stocked are not actionable here.
    candidates = []
    for forecast in demand_forecasts:
        inventory_item = inventory_by_sku.get(forecast["item_sku"])
        if not inventory_item:
            continue
        shortage = max(forecast["forecasted_demand"] - inventory_item["quantity_on_hand"], 0)
        if shortage <= 0:
            continue
        candidates.append({
            "sku": inventory_item["sku"],
            "name": inventory_item["name"],
            "category": inventory_item["category"],
            "warehouse": inventory_item["warehouse"],
            "quantity_on_hand": inventory_item["quantity_on_hand"],
            "forecasted_demand": forecast["forecasted_demand"],
            "shortage": shortage,
            "unit_cost": inventory_item["unit_cost"],
            "lead_time_days": _lead_time_days_for(inventory_item["category"]),
        })

    candidates.sort(key=lambda c: c["shortage"], reverse=True)

    recommendations = []
    remaining_budget = max(budget, 0.0)
    for c in candidates:
        if remaining_budget <= 0:
            break
        full_cost = c["shortage"] * c["unit_cost"]
        if full_cost <= remaining_budget:
            suggested_quantity = c["shortage"]
        else:
            # Partial fill: spend whatever's left on as many units as fit.
            suggested_quantity = int(remaining_budget // c["unit_cost"])
            if suggested_quantity <= 0:
                continue
        line_total = round(suggested_quantity * c["unit_cost"], 2)
        remaining_budget -= line_total
        recommendations.append({
            **c,
            "suggested_quantity": suggested_quantity,
            "line_total": line_total,
        })
    return recommendations


@app.post("/api/restocking/orders", response_model=SubmittedRestockingOrder)
def submit_restocking_order(payload: CreateRestockingOrderRequest):
    """Submit a restocking order. Persists to an in-memory list (server-restart wipes)."""
    if not payload.items:
        raise HTTPException(status_code=400, detail="At least one item is required")

    submitted_at = datetime.now()
    # Expected delivery is gated by the slowest item in the order
    max_lead = max(item.lead_time_days for item in payload.items)
    expected_delivery = submitted_at + timedelta(days=max_lead)
    total_value = round(sum(item.line_total for item in payload.items), 2)

    # Per-year-and-sequence order number, scanned out of the existing in-memory list
    year = submitted_at.year
    seq = sum(1 for o in submitted_restocking_orders if o["order_number"].startswith(f"RST-{year}-")) + 1
    order_number = f"RST-{year}-{seq:04d}"

    order = {
        "id": str(len(submitted_restocking_orders) + 1),
        "order_number": order_number,
        "submitted_date": submitted_at.isoformat(timespec="seconds"),
        "expected_delivery": expected_delivery.isoformat(timespec="seconds"),
        "total_value": total_value,
        "items": [item.model_dump() for item in payload.items],
        "status": "Submitted",
    }
    submitted_restocking_orders.append(order)
    return order


@app.get("/api/restocking/orders", response_model=List[SubmittedRestockingOrder])
def list_restocking_orders():
    """Return all submitted restocking orders, newest first."""
    return list(reversed(submitted_restocking_orders))


# In-memory user-task store. The frontend (App.vue → TasksModal) loads/edits
# user-created tasks via these endpoints alongside the per-user mock tasks
# defined in useAuth.js. Restarting the server clears the list.
class Task(BaseModel):
    id: int
    title: str
    priority: Optional[str] = "medium"
    dueDate: Optional[str] = None
    status: str = "pending"


class CreateTaskRequest(BaseModel):
    title: str
    priority: Optional[str] = "medium"
    dueDate: Optional[str] = None


_user_tasks: List[dict] = []
_next_task_id: int = 1000


@app.get("/api/tasks", response_model=List[Task])
def list_tasks():
    """Return user-created tasks, newest first."""
    return list(reversed(_user_tasks))


@app.post("/api/tasks", response_model=Task)
def create_task(payload: CreateTaskRequest):
    global _next_task_id
    task = {
        "id": _next_task_id,
        "title": payload.title,
        "priority": payload.priority or "medium",
        "dueDate": payload.dueDate,
        "status": "pending",
    }
    _next_task_id += 1
    _user_tasks.append(task)
    return task


@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int):
    for idx, t in enumerate(_user_tasks):
        if t["id"] == task_id:
            _user_tasks.pop(idx)
            return {"deleted": task_id}
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


@app.patch("/api/tasks/{task_id}", response_model=Task)
def toggle_task(task_id: int):
    for t in _user_tasks:
        if t["id"] == task_id:
            t["status"] = "completed" if t["status"] == "pending" else "pending"
            return t
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
