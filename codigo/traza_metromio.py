# traza_metromio.py - Simula los 4 saltos de MetroMIO-IoT con OpenTelemetry
import time
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.propagate import inject, extract

provider = TracerProvider(resource=Resource.create({"service.name": "metromio-ingesta", "service.namespace": "metromio"}))
provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("metromio.lab")

def salto(nombre, headers_entrantes, segundos, atributos=None):
    ctx = extract(headers_entrantes)                       # 1) EXTRAER el traceparent entrante
    with tracer.start_as_current_span(nombre, context=ctx) as span:
        for k, v in (atributos or {}).items():
            span.set_attribute(k, v)
        time.sleep(segundos)                               # trabajo simulado del salto
        salida = {}
        inject(salida)                                     # 2) INYECTAR para el siguiente salto
        print(">>", nombre, "-> traceparent enviado:", salida["traceparent"])
    return salida

with tracer.start_as_current_span("root.bus-telemetria") as root:
    root.set_attribute("bus.id", "MIO-T31-0457")
    h = {}
    inject(h)
    print(">> root -> traceparent enviado:", h["traceparent"])
    h = salto("salto1.edge-mqtt-k3s", h, 0.012)
    h = salto("salto2.api-gateway-mtls", h, 0.008)
    h = salto("salto3.ingesta-service", h, 0.045)
    h = salto("salto4.timescaledb.insert", h, 0.003, {"db.system": "postgresql", "db.operation": "INSERT"})
