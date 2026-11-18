# ingesta_flask.py - Microservicio de ingesta con propagación W3C y log correlacionado
import logging
from flask import Flask, request
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.propagate import extract, inject

provider = TracerProvider(resource=Resource.create({"service.name": "ingesta-service", "service.namespace": "metromio"}))
provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(provider)
app = Flask(__name__); logging.basicConfig(level=logging.INFO)
tracer = trace.get_tracer("ingesta-service")

@app.post("/telemetria")
def recibir():
    ctx = extract({k.lower(): v for k, v in request.headers.items()})     # 1. extraer traceparent entrante
    with tracer.start_as_current_span("ingesta.procesar", context=ctx, kind=trace.SpanKind.SERVER) as span:
        d = request.json
        trace_id = format(span.get_span_context().trace_id, "032x")
        span.set_attribute("bus.id", d["bus_id"]); span.set_attribute("tenant", "metromio")
        with tracer.start_as_current_span("timescaledb.insert", kind=trace.SpanKind.CLIENT) as db:
            db.set_attribute("db.system", "postgresql")
            carrier = {}; inject(carrier)                                  # 2. contexto del span hijo
            sql = f"/*traceparent='{carrier['traceparent']}'*/ INSERT INTO telemetria VALUES (%s,%s,%s)"
            print(">> SQL:", sql, "| params:", (d["bus_id"], d["lat"], d["lon"]))   # BD simulada
        app.logger.info({"msg": "guardada", "trace_id": trace_id, "bus_id": d["bus_id"]})
        return {"status": "ok", "trace_id": trace_id}, 201

if __name__ == "__main__":
    c = app.test_client()
    tp = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
    r = c.post("/telemetria", json={"bus_id": "MIO-T31-0457", "lat": 3.4516, "lon": -76.5320}, headers={"traceparent": tp})
    print("HTTP", r.status_code, r.get_json())
