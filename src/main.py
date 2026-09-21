from fastapi import FastAPI

app = FastAPI(
    title="Huellitas de Amor API",
    description="API para la gestión de mascotas, refugios y adopciones.",
    version="0.1.0",
)


@app.get("/")
async def root():
    return {
        "message": "Bienvenido a Huellitas de Amor API"
    }
