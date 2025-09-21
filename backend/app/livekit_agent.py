import logging
import os
import pathlib
from livekit.agents import (
    NOT_GIVEN,
    Agent,
    AgentFalseInterruptionEvent,
    AgentSession,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RoomInputOptions,
    RunContext,
    WorkerOptions,
    cli,
    metrics,
)
from livekit.agents.llm import function_tool
from livekit.agents.voice.events import CloseEvent, ErrorEvent
from livekit.agents.utils.audio import audio_frames_from_file
from livekit.plugins import cartesia, deepgram, noise_cancellation, openai, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from prompt import SYSTEM_PROMPT
from crud import create_ticket, edit_ticket
from db import SessionLocal
from typing import Optional

logger = logging.getLogger("agent")

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=SYSTEM_PROMPT,
        )

    @function_tool
    async def create_ticket(
        self, 
        context: RunContext, 
        name: str,
        email: str,
        phone: str,
        address: str,
        issue: str,
        price: float
    ):
        """Use this tool to create a support ticket.
        
        IMPORTANT: ALL TEXT DATA MUST BE IN ENGLISH BEFORE CALLING THIS FUNCTION.
        Translate any non-English names, addresses, or issue descriptions to English.

        Args:
            name: Customer's full name (MUST BE IN ENGLISH)
            email: Customer's email address
            phone: Customer's phone number
            address: Customer's address (MUST BE IN ENGLISH)
            issue: Description of the technical issue (MUST BE IN ENGLISH)
            price: Service fee for the issue
        """

        logger.info(f"Creating ticket for {name} with issue: {issue}")
        logger.info(f"Ticket details - Name: {name}, Address: {address}, Issue: {issue}")

        db = SessionLocal()
        try:
            if not all([name, email, phone, address, issue]):
                raise ValueError("All required fields must be provided")
            
            if price <= 0:
                raise ValueError("Price must be greater than 0")

            ticket = create_ticket(
                db=db,
                name=name,
                email=email,
                phone=phone,
                address=address,
                issue=issue,
                price=price
            )
            logger.info(f"Ticket {ticket.id} created successfully")
            return f"Ticket created successfully with ID: {ticket.id}"
        except Exception as e:
            logger.error(f"Error creating ticket: {e}")
            return f"Error creating ticket: {str(e)}"
        finally:
            try:
                db.close()
            except Exception as close_error:
                logger.error(f"Error closing database connection: {close_error}")
    
    @function_tool
    async def edit_ticket(
        self, 
        context: RunContext, 
        ticket_id: Optional[int] = NOT_GIVEN,
        name: Optional[str] = NOT_GIVEN,
        email: Optional[str] = NOT_GIVEN,
        phone: Optional[str] = NOT_GIVEN,
        address: Optional[str] = NOT_GIVEN,
        issue: Optional[str] = NOT_GIVEN,
        price: Optional[float] = NOT_GIVEN,
    ):
        """Use this tool to edit an existing support ticket.
        
        IMPORTANT: ALL TEXT DATA MUST BE IN ENGLISH BEFORE CALLING THIS FUNCTION.
        Translate any non-English names, addresses, or issue descriptions to English.

        Args:
            ticket_id: The ID of the ticket to edit
            name: Customer's full name (MUST BE IN ENGLISH, optional)
            email: Customer's email address (optional)
            phone: Customer's phone number (optional)
            address: Customer's address (MUST BE IN ENGLISH, optional)
            issue: Description of the technical issue (MUST BE IN ENGLISH, optional)
            price: Service fee for the issue (optional)
        """

        logger.info(f"Editing ticket {ticket_id}")
        if name != NOT_GIVEN:
            logger.info(f"Updating name to: {name}")
        if address != NOT_GIVEN:
            logger.info(f"Updating address to: {address}")
        if issue != NOT_GIVEN:
            logger.info(f"Updating issue to: {issue}")

        db = SessionLocal()
        try:
            if ticket_id is None or ticket_id <= 0:
                raise ValueError("Valid ticket ID is required")

            ticket = edit_ticket(
                db=db,
                ticket_id=ticket_id,
                name=name,
                email=email,
                phone=phone,
                address=address,
                issue=issue,
                price=price
            )

            if ticket:
                logger.info(f"Ticket {ticket_id} updated successfully")
                return f"Ticket {ticket_id} updated successfully"
            else:
                logger.warning(f"Ticket {ticket_id} not found")
                return f"Ticket {ticket_id} not found"
                
        except ValueError as ve:
            logger.error(f"Validation error editing ticket: {ve}")
            return f"There's an issue with the ticket information: {str(ve)}"
            
        except Exception as e:
            logger.error(f"Error editing ticket {ticket_id}: {e}")
            return f"Error editing ticket: {str(e)}"
        finally:
            try:
                db.close()
            except Exception as close_error:
                logger.error(f"Error closing database connection: {close_error}")

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    print("Entrypoint called")
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    session = AgentSession(
        llm=openai.LLM(model="gpt-4o-mini"),
        stt=deepgram.STT(model="nova-3", language="en-US"),
        tts=cartesia.TTS(voice="6f84f4b8-58a2-430c-8c79-688dad597532"),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    error_audio_path = os.path.join(pathlib.Path(__file__).parent.absolute(), "error_message.ogg")

    @session.on("error")
    def on_error(ev: ErrorEvent):
        logger.error(f"Agent error occurred: {ev.error} from {ev.source}")
        
        if ev.error.recoverable:
            logger.info("Error is recoverable, continuing session")
            return

        logger.warning(f"Session encountered unrecoverable error: {ev.error}")

        try:
            if os.path.exists(error_audio_path):
                session.say(
                    "I'm experiencing technical difficulties. Please try reconnecting in a moment.",
                    audio=audio_frames_from_file(error_audio_path),
                    allow_interruptions=False,
                )
            else:
                session.say(
                    "I'm experiencing technical difficulties. Please try reconnecting in a moment.",
                    allow_interruptions=False,
                )
        except Exception as say_error:
            logger.error(f"Could not inform user about error: {say_error}")

        if isinstance(ev.source, (openai.LLM, cartesia.TTS)):
            logger.info("Attempting to recover from LLM/TTS error")
            ev.error.recoverable = True
            return

        if isinstance(ev.source, deepgram.STT):
            logger.info("Attempting to recover from STT error by resetting agent")
            try:
                session.update_agent(session.current_agent)
                ev.error.recoverable = True
                return
            except Exception as reset_error:
                logger.error(f"Failed to reset agent: {reset_error}")

        logger.error("Error is unrecoverable, session will close")

    @session.on("close")
    def on_close(ev: CloseEvent):
        logger.info(f"Session is closing. Reason: {ev.reason if hasattr(ev, 'reason') else 'Unknown'}")
        
        try:
            db = SessionLocal()
            db.close()
            logger.info("Database connections cleaned up")
        except Exception as cleanup_error:
            logger.error(f"Error during cleanup: {cleanup_error}")

        logger.info(f"Session ended for room: {ctx.room.name}")

    @session.on("agent_false_interruption")
    def _on_agent_false_interruption(ev: AgentFalseInterruptionEvent):
        logger.info("False positive interruption detected, resuming speech")
        try:
            session.generate_reply(instructions=ev.extra_instructions or None)
        except Exception as resume_error:
            logger.error(f"Failed to resume after false interruption: {resume_error}")



    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
