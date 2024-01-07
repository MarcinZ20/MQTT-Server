from connection import Server

server = Server([('admin', 'admin')], auth=True)

server.run()
