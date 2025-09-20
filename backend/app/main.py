import asyncio
import uvicorn
import sys
import os
from multiprocessing import Process
from livekit.agents import WorkerOptions, cli
from livekit_agent import entrypoint, prewarm
from api_server import app

def run_api_server():
    """Run the FastAPI server"""
    print("🚀 Starting FastAPI server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)

def run_livekit_agent():
    """Run the LiveKit agent with proper CLI simulation"""
    print("🤖 Starting LiveKit Agent...")
    
    original_argv = sys.argv.copy()
    sys.argv = ['livekit-agent', 'dev']
    
    try:
        cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
    except Exception as e:
        print(f"❌ LiveKit Agent error: {e}")
    finally:
        sys.argv = original_argv

if __name__ == "__main__":
    required_env_vars = ['LIVEKIT_API_KEY', 'LIVEKIT_API_SECRET', 'LIVEKIT_URL']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("📝 Please create a .env.local file with your LiveKit configuration:")
        for var in missing_vars:
            print(f"   {var}=your_value_here")
        sys.exit(1)
    
    print("=" * 50)
    print("🎯 DeskHelp Bot - Starting Services")
    print("=" * 50)
    
    api_process = Process(target=run_api_server)
    agent_process = Process(target=run_livekit_agent)
    
    try:
        api_process.start()
        agent_process.start()
        
        print("✅ Both services started successfully!")
        print("📡 FastAPI: http://localhost:8000")
        print("🤖 LiveKit Agent: Connected to your LiveKit instance")
        print("\n💡 Press Ctrl+C to stop all services")
        
        # Wait for both processes
        api_process.join()
        agent_process.join()
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down services...")
        api_process.terminate()
        agent_process.terminate()
        
        # Wait for clean shutdown
        api_process.join(timeout=5)
        agent_process.join(timeout=5)
        
        print("✅ All services stopped cleanly")
    except Exception as e:
        print(f"❌ Error: {e}")
        api_process.terminate()
        agent_process.terminate()
        sys.exit(1)