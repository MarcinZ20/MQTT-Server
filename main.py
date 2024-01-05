from connection import Server

server = Server([('admin', 'admin')], auth=False)

server.run()
