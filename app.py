#!/usr/bin/python3
import signal
from gevent import signal as gsignal
from gevent.pywsgi import WSGIServer
from pyuval.app import createOtpServer

app = createOtpServer('server.yaml')
#app.run('0.0.0.0')
httpServer = WSGIServer(('127.0.0.1', 5000), app)
gsignal(signal.SIGINT, httpServer.stop)
httpServer.serve_forever()