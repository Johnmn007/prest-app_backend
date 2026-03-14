from app.database.base import Base
from app.models.user import User
from app.models.client import Client
from app.models.loan import Loan, Installment # Asegúrate de que Loan e Installment vengan de aquí
from app.models.payment import Payment
from app.models.refinancing import Refinancing
from app.models.route import Route
from app.models.route_client import RouteClient
from app.models.expense import Expense
from app.models.audit_log import AuditLog