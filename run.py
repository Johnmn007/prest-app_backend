import uvicorn
import os
from app.config.settings import settings

if __name__ == "__main__":
    # Railway deployment configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    # Only reload in development
    reload = settings.ENVIRONMENT == "development"
    
    uvicorn.run(
        "app.main:app", 
        host=host, 
        port=port, 
        reload=reload,
        # Production optimizations
        workers=int(os.getenv("WEB_CONCURRENCY", 1)) if not reload else 1,
        log_level="info" if settings.ENVIRONMENT == "production" else "debug",
        access_log=True,
        timeout_keep_alive=30,
    )
