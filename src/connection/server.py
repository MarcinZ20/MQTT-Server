import asyncio
import logging
import sys
import traceback

from src.connection.client import Client

logging.basicConfig(
    level=logging.DEBUG,
    format='[{asctime}] [{levelname:<8}] {name}: {message}',
    datefmt='%Y-%m-%d %H:%M:%S',
    style='{'
)

log = logging.getLogger(__name__)


class Server:
    def __init__(self, users: list[tuple[str, str]]):  # TODO: update this to use the auth module
        self._client_tasks: set[asyncio.Task] = set()
        self.users = users

    def run(self):
        """Starts the server."""

        try:
            asyncio.run(self._start())
        except KeyboardInterrupt:
            return

    async def _start(self):
        """The async startup function."""

        server = await asyncio.start_server(self._handle_connection, 'localhost', 1883)
        server_auth = await asyncio.start_server(self._handle_auth_connection, 'localhost', 1884)

        log.info('Server started!')

        async with server, server_auth:
            await asyncio.gather(server.serve_forever(), server_auth.serve_forever())

    async def _handle_new_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        auth_required: bool
    ):
        """Handles a new client connecting to the server."""

        task = asyncio.current_task()
        self._client_tasks.add(task)

        client = Client(self, reader, writer, auth_required)

        try:
            await client.serve()
        except Exception as e:
            print(traceback.format_exc(), file=sys.stderr)
        finally:
            await client.close()
            try:
                self._client_tasks.remove(task)
            except KeyError:
                pass

    async def _handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handles a non-authenticated connection to the server."""

        await self._handle_new_client(reader, writer, False)

    async def _handle_auth_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handles an authenticated connection to the server."""

        await self._handle_new_client(reader, writer, True)
