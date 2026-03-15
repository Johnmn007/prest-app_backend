import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config.settings import settings
from app.routes.auth_router import router as auth_router
from app.routes.client_router import router as client_router
from app.routes.loan_router import router as loan_router
from app.routes.installment_router import router as installment_router
from app.routes.payment_router import router as payment_router
from app.routes.refinancing_router import router as refinancing_router
from app.routes.dashboard_router import router as dashboard_router
from app.routes.route_router import router as routes_router
from app.routes.expense_router import router as expense_router

# Logging estructurado
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Dilver — Sistema de Préstamos Gota a Gota",
    description="API para gestión de préstamos, cobranzas, morosidad y reportes.",
    version="1.0.0",
    # Ocultar docs en producción
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)

# CORS — solo orígenes conocidos
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
    max_age=600,
)

# Handler global de errores no controlados
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

# Routers
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
    return {"status": "ok", "environment": settings.ENVIRONMENT}
