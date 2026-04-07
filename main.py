from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api import api_router
from app.db.database import init_db
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## Finance Dashboard API

A role-based finance management backend built with **FastAPI**, **SQLite**, and **JWT**.

### Roles
| Role | Permissions |
|---|---|
| `viewer` | Read own transactions & scoped dashboard summary |
| `analyst` | Read all records, create/edit/delete own transactions, full dashboard |
| `admin` | Full access — manage users, all transactions, audit logs |

### Quick Start
1. **Register** → `POST /api/v1/auth/register`
2. **Login** → `POST /api/v1/auth/login` — copy the `access_token`
3. Click **Authorize** above, paste the token
4. Explore!

> **Default admin:** `admin@finance.com` / `admin123`
    """,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middleware (order matters — outermost registered last) ────────────────────
app.add_middleware(CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)


# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )


# ── Startup ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    init_db()
    _seed_admin()


def _seed_admin():
    """Create a default admin user on first boot if the users table is empty."""
    from app.db.database import SessionLocal
    from app.models.user import User, UserRole
    from app.core.security import get_password_hash

    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            admin = User(
                full_name="Super Admin",
                email="admin@finance.com",
                hashed_password=get_password_hash("admin123"),
                role=UserRole.admin,
                is_active=True,
            )
            db.add(admin)
            db.commit()
            print("✅ Default admin seeded → admin@finance.com / admin123")
    finally:
        db.close()


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(api_router)


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
def health_check():
    """Liveness probe."""
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}