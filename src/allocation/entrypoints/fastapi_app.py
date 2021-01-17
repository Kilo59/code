from datetime import datetime, date
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse
from allocation.domain import commands
from allocation.domain.model import OrderLine
from allocation.service_layer.handlers import InvalidSku
from allocation import bootstrap, views

app = FastAPI(__name__)
bus = bootstrap.bootstrap()

class Batch(BaseModel):
    ref: str
    sku: str
    qty: int
    eta: date = None 


@app.post("/add_batch", status_code=201, response_class=PlainTextResponse)
def add_batch(batch: Batch):
    cmd = commands.CreateBatch(
       batch.ref, batch.sku, batch.qty, batch.eta,
    )
    bus.handle(cmd)
    return "OK"


@app.post("/allocate", status_code=202)
def allocate_endpoint(order_line: OrderLine):
    try:
        cmd = commands.Allocate(
            order_line.orderid, order_line.sku, order_line.qty,
        )
        bus.handle(cmd)
    except InvalidSku as e:

        return JSONResponse(str(e), status_code=400)

    return {"message": "OK"}


@app.get("/allocations/{orderid}", status_code=200)
def allocations_view_endpoint(orderid: str):
    result = views.allocations(orderid, bus.uow)
    if not result:
        return 'not found', 404
    return result
