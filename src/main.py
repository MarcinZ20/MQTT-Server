from src.connection.server import Server

server = Server([('admin', 'admin')])

server.run()
