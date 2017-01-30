#!/usr/bin/env python
'''
World's simplest multi-threaded socket server for testing
git2dot.py output.

Run it like this:

   $ webserver.py 8090

You can then access the contents of the local directory using
http://localhost:8090.
'''
import sys
import SocketServer
import BaseHTTPServer
import SimpleHTTPServer

class ThreadingHTTPServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    pass

assert len(sys.argv) == 2
port = int(sys.argv[1])
httpd = ThreadingHTTPServer(('', port), SimpleHTTPServer.SimpleHTTPRequestHandler)
try:
    print('Serving on port {}'.format(port))
    httpd.serve_forever()
except KeyboardInterrupt:
    print('Done.')
    
