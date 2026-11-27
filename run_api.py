from uvicorn import Config, Server

from app.logging import setup_logging
from app.main import app

setup_logging()

if __name__ == "__main__":
    config = Config(
        app=app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=True,
    )

    server = Server(config=config)
    print("Starting Payment Processing API Server...")
    
    server.run()
