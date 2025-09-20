import asyncio
import uvicorn
from multiprocessing import Process
from livekit.agents import WorkerOptions, cli
from livekit_agent import entrypoint, prewarm
from api_server import app

def run_api_server():
    """Run the FastAPI server"""
    uvicorn.run(app, host="0.0.0.0", port=8000)

def run_livekit_agent():
    """Run the LiveKit agent"""
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))

if __name__ == "__main__":
    api_process = Process(target=run_api_server)
    agent_process = Process(target=run_livekit_agent)
    
    api_process.start()
    agent_process.start()
    
    try:
        api_process.join()
        agent_process.join()
    except KeyboardInterrupt:
        api_process.terminate()
        agent_process.terminate()
