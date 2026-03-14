from pydantic import BaseModel
from typing import Optional

class DashboardMetricsResponse(BaseModel):
    total_portfolio: float
    total_active_loans: int
    total_delinquent_clients: int
    daily_income: float
    estimated_profit: float
