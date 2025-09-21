import logging

from dotenv import load_dotenv
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
from livekit.plugins import cartesia, deepgram, noise_cancellation, openai, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from prompt import SYSTEM_PROMPT
from crud import create_ticket, edit_ticket
from db import SessionLocal
from typing import Optional

logger = logging.getLogger("agent")

load_dotenv(".env.local")

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
            db.close()
    
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
        except Exception as e:
            logger.error(f"Error editing ticket {ticket_id}: {e}")
            return f"Error editing ticket: {str(e)}"
        finally:
            db.close()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    print("Entrypoint called")
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using OpenAI, Cartesia, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all providers at https://docs.livekit.io/agents/integrations/llm/
        llm=openai.LLM(model="gpt-4o-mini"),
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all providers at https://docs.livekit.io/agents/integrations/stt/
        stt=deepgram.STT(model="nova-3", language="en-US"),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all providers at https://docs.livekit.io/agents/integrations/tts/
        tts=cartesia.TTS(voice="6f84f4b8-58a2-430c-8c79-688dad597532"),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
    )

    # To use a realtime model instead of a voice pipeline, use the following session setup instead:
    # session = AgentSession(
    #     # See all providers at https://docs.livekit.io/agents/integrations/realtime/
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # sometimes background noise could interrupt the agent session, these are considered false positive interruptions
    # when it's detected, you may resume the agent's speech
    @session.on("agent_false_interruption")
    def _on_agent_false_interruption(ev: AgentFalseInterruptionEvent):
        logger.info("false positive interruption, resuming")
        session.generate_reply(instructions=ev.extra_instructions or None)

    # Metrics collection, to measure pipeline performance
    # For more information, see https://docs.livekit.io/agents/build/metrics/
    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/integrations/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/integrations/avatar/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            # LiveKit Cloud enhanced noise cancellation
            # - If self-hosting, omit this parameter
            # - For telephony applications, use `BVCTelephony` for best results
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    # Join the room and connect to the user
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
