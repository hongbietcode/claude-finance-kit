"""Base WebSocket client for market data streaming."""

import asyncio
import logging
import traceback
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)

try:
    import websockets
    import websockets.exceptions
    _WEBSOCKETS_AVAILABLE = True
except ImportError:
    _WEBSOCKETS_AVAILABLE = False


class BaseWebSocketClient(ABC):
    """Abstract WebSocket client for streaming market data.

    Concrete subclasses must implement:
        _send_initial_messages() — source-specific subscription logic.
        _parse_message(message)  — source-specific message parsing.

    Processors are objects with an async ``process(data)`` method that receive
    parsed message dicts as they arrive.

    Args:
        uri: WebSocket endpoint URI.
        ping_interval: Seconds between keep-alive ping messages (default 25).
    """

    def __init__(self, uri: str, ping_interval: int = 25) -> None:
        if not _WEBSOCKETS_AVAILABLE:
            raise ImportError("websockets is required for streaming: pip install websockets")
        self.uri = uri
        self.ping_interval = ping_interval
        self.websocket: Any = None
        self.running: bool = False
        self.processors: list[Any] = []
        self._ping_task: asyncio.Task | None = None  # type: ignore[type-arg]
        self._handler_task: asyncio.Task | None = None  # type: ignore[type-arg]

    def add_processor(self, processor: Any) -> None:
        """Register a data processor.

        Args:
            processor: Object with an async ``process(data: dict)`` method.
        """
        self.processors.append(processor)

    async def _send_ping(self) -> None:
        """Send periodic ping messages to keep the connection alive."""
        while self.running:
            if self.websocket:
                try:
                    await self.websocket.send("2")
                    logger.debug("Ping sent")
                except Exception as exc:
                    logger.error("Error sending ping: %s\n%s", exc, traceback.format_exc())
            await asyncio.sleep(self.ping_interval)

    @abstractmethod
    async def _send_initial_messages(self) -> None:
        """Send source-specific subscription messages after connection."""
        raise NotImplementedError

    @abstractmethod
    def _parse_message(self, message: str) -> dict[str, Any] | None:
        """Parse a raw WebSocket message.

        Args:
            message: Raw string received from the server.

        Returns:
            Parsed data dict, or None to discard the message.
        """
        raise NotImplementedError

    def _on_connection_closed(self) -> None:
        """Hook called when the WebSocket connection closes unexpectedly."""

    def _on_handler_done(self, task: "asyncio.Task[None]") -> None:
        try:
            task.result()
        except asyncio.CancelledError:
            logger.info("Message handler task cancelled")
        except Exception as exc:
            logger.error("Message handler task failed: %s\n%s", exc, traceback.format_exc())
        finally:
            self.running = False
            logger.info("Message handler task completed")

    async def _handle_messages(self) -> None:
        """Receive and dispatch messages until the connection closes."""
        logger.info("Message handler started")
        count = 0
        while self.running and self.websocket:
            try:
                raw = await self.websocket.recv()
                count += 1
                logger.debug("[MSG #%d] %.80s", count, raw)
                parsed = self._parse_message(raw)
                if parsed:
                    for processor in self.processors:
                        try:
                            await processor.process(parsed)
                        except Exception as exc:
                            logger.error(
                                "Processor %s error: %s\n%s",
                                type(processor).__name__,
                                exc,
                                traceback.format_exc(),
                            )
            except websockets.exceptions.ConnectionClosed as exc:
                logger.warning("WebSocket connection closed: %s", exc)
                self._on_connection_closed()
                break
            except Exception as exc:
                logger.error("Error handling message: %s\n%s", exc, traceback.format_exc())

    async def connect(self) -> None:
        """Connect to the WebSocket server and start background tasks.

        Returns immediately after connection is established; message handling
        and ping run as background asyncio tasks.

        Raises:
            Exception: Re-raises any connection error after cleanup.
        """
        if self.running:
            logger.warning("Already connected or connection in progress")
            return
        self.running = True
        try:
            logger.info("Connecting to %s…", self.uri)
            self.websocket = await websockets.connect(self.uri)
            logger.info("Connected to %s", self.uri)
            await self._send_initial_messages()
            self._ping_task = asyncio.create_task(self._send_ping())
            self._handler_task = asyncio.create_task(self._handle_messages())
            self._handler_task.add_done_callback(self._on_handler_done)
            logger.info("Background tasks started")
        except Exception as exc:
            logger.error("Connection error: %s\n%s", exc, traceback.format_exc())
            self.running = False
            if self.websocket:
                await self.websocket.close()
            self.websocket = None
            raise

    async def disconnect(self) -> None:
        """Disconnect and cancel all background tasks."""
        logger.info("Disconnecting…")
        self.running = False
        for task in (self._ping_task, self._handler_task):
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        self._ping_task = None
        self._handler_task = None
        if self.websocket:
            try:
                await self.websocket.close()
                logger.info("Connection closed")
            except Exception as exc:
                logger.error("Error closing connection: %s\n%s", exc, traceback.format_exc())
            finally:
                self.websocket = None
        logger.info("Disconnected")

    def is_connected(self) -> bool:
        """Return True if the client is active and the handler task is running."""
        return (
            self.websocket is not None
            and self.running
            and self._handler_task is not None
            and not self._handler_task.done()
        )

    async def wait_until_disconnected(self) -> None:
        """Block until the message handler task completes."""
        if self._handler_task:
            try:
                await self._handler_task
            except asyncio.CancelledError:
                pass

    async def send_message(self, message: str) -> None:
        """Send a raw message to the WebSocket server.

        Args:
            message: Raw string to send.
        """
        if self.websocket:
            try:
                await self.websocket.send(message)
                logger.debug("Sent: %.50s…", message)
            except Exception as exc:
                logger.error("Error sending message: %s\n%s", exc, traceback.format_exc())
        else:
            logger.error("Cannot send message: not connected")
