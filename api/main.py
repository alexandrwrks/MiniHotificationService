from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api import orders, services, users
from common.errors import AppError
from database.config import engine
from messaging.broker import (
    connect_rabbitmq,
    declare_notification_queue,
    declare_order_exchange,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    connection = await connect_rabbitmq()
    try:
        channel = await connection.channel()
        exchange = await declare_order_exchange(channel)
        await declare_notification_queue(channel, exchange)
        app.state.order_exchange = exchange
        yield
    finally:
        await connection.close()
        await engine.dispose()


app = FastAPI(title="Order notifications", lifespan=lifespan)
app.include_router(users.router)
app.include_router(services.router)
app.include_router(orders.router)


@app.exception_handler(AppError)
async def handle_app_error(request: Request, error: AppError):
    status_code = {
        "not_found": 404,
        "forbidden": 403,
        "conflict": 409,
        "invalid": 422,
        "unavailable": 503,
    }[error.code]
    return JSONResponse(
        status_code=status_code, content={"detail": error.details or error.message}
    )
