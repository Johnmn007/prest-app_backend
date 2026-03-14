from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.auth_router import router as auth_router
from app.routes.client_router import router as client_router
from app.routes.loan_router import router as loan_router
from app.routes.installment_router import router as installment_router
from app.routes.payment_router import router as payment_router
from app.routes.refinancing_router import router as refinancing_router
from app.routes.dashboard_router import router as dashboard_router
from app.routes.route_router import router as routes_router
from app.routes.expense_router import router as expense_router

app = FastAPI(
    title="Sistema de Administración de Préstamos 'Gota a Gota'",
    description="Backend API para la gestión de préstamos, cobranzas, morosidad y reportes.",
    version="1.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*",
    "http://localhost:5173",
    "",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(client_router)
app.include_router(loan_router)
app.include_router(installment_router)
app.include_router(payment_router)
app.include_router(refinancing_router)
app.include_router(dashboard_router)
app.include_router(routes_router)
app.include_router(expense_router)

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "API Gota a Gota is running smoothly"}
