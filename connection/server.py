import asyncio
import logging
import sys
import traceback
import os

from authentication.Auth import Auth
from processing import TopicManager
from dotenv import load_dotenv

from .client import Client

logging.basicConfig(
    level=logging.DEBUG,
    format='[{asctime}] [{levelname:<8}] {name}: {message}',
    datefmt='%Y-%m-%d %H:%M:%S',
    style='{'
)

log = logging.getLogger(__name__)

load_dotenv()

class Server:
    def __init__(self, auth: bool):
        self._client_tasks: set[asyncio.Task] = set()
        self._clients: dict[str, Client] = dict()
        self.topic_manager = TopicManager()
        self._auth = auth
        self._message_count = 0

        if self._auth:
            log.info('Authentication is enabled')
            self.auth_module = Auth(os.getenv('PASSWD_FILE_PATH'))
            self.auth_module.create_passwd_file()

    def run(self):
        """Starts the server."""

        try:
            asyncio.run(self._start())
        except KeyboardInterrupt:
            return

    def get_next_message_id(self) -> int:
        """Gets a message id for the next message."""

        self._message_count += 1
        return self._message_count

    def _get_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        auth: bool,
        address: str
    ) -> Client:
        """Gets the client object in case a disconnect happened or creates a new one."""

        client = self._clients.get(address)
        if client is None:
            client = Client(self, reader, writer, auth, address)
            self._clients[address] = client

        return client

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

        client = self._get_client(reader, writer, self._auth, address)

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
