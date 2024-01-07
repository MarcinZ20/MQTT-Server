import asyncio
import logging
import sys
import traceback

from processing import TopicManager
from .client import Client

logging.basicConfig(
    level=logging.DEBUG,
    format='[{asctime}] [{levelname:<8}] {name}: {message}',
    datefmt='%Y-%m-%d %H:%M:%S',
    style='{'
)

log = logging.getLogger(__name__)


class Server:
    def __init__(self, users: list[tuple[str, str]], auth: bool):  # TODO: update this to use the auth module
        self._client_tasks: set[asyncio.Task] = set()
        self.users = users
        self.clients: dict[str, Client] = dict()
        self.topic_manager = TopicManager()
        self._auth = auth

    def run(self):
        """Starts the server."""

        try:
            asyncio.run(self._start())
        except KeyboardInterrupt:
            return

    def get_client(self, reader, writer, auth, address):
        client = self.clients.get(address)
        if client:
            return client
        else:
            new_client = Client(self, reader, writer, auth, address)
            self.clients[address] = new_client
            return new_client

    async def _start(self):
        """The async startup function."""

        port = 1884 if self._auth else 1883

        server = await asyncio.start_server(self._handle_connection, 'localhost', port)

        log.info('Server started!')

        async with server:
            await server.serve_forever()

    async def _handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handles a new connection to the server."""

        task = asyncio.current_task()
        self._client_tasks.add(task)

        ip, port = writer.get_extra_info('peername')
        address = f'{ip}:{port}'

        client = self.get_client(reader, writer, self._auth, address)

        try:
            await client.serve()
        except Exception as e:
            print(traceback.format_exc(), file=sys.stderr)
        finally:
            if not client.is_closed():
                await client.close()

            try:
                self._client_tasks.remove(task)
            except KeyError:
                pass
