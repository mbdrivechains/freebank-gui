#!/usr/bin/env python3
"""
Simple CORS proxy for the FreeBank PWA

This proxy sits between the PWA and freebankd, adding CORS headers
so browser-based apps can make RPC calls.

Usage:
    python3 proxy.py --rpc-host localhost --rpc-port 18457 --rpc-user rpcuser --rpc-password rpcpassword

The proxy runs on port 3001 by default. Configure the PWA to connect to this proxy.
"""

import argparse
import base64
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import urllib.error
import ssl

class CORSProxyHandler(BaseHTTPRequestHandler):
    rpc_url = None
    rpc_auth = None

    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

    def do_OPTIONS(self):
        """Handle preflight CORS requests"""
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_POST(self):
        """Forward RPC request to freebankd"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)

            # Create request to freebankd
            req = urllib.request.Request(
                self.rpc_url,
                data=body,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Basic {self.rpc_auth}',
                },
                method='POST'
            )

            # Forward to freebankd
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            with urllib.request.urlopen(req, timeout=30) as response:
                result = response.read()

            # Send response with CORS headers
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(result)

        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(e.read())
        except Exception as e:
            self.send_response(500)
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())

    def log_message(self, format, *args):
        """Custom logging"""
        print(f"[PROXY] {args[0]}")


def main():
    parser = argparse.ArgumentParser(description='CORS proxy for FreeBank RPC')
    parser.add_argument('--port', type=int, default=3001, help='Proxy port (default: 3001)')
    parser.add_argument('--rpc-host', default='localhost', help='freebankd host')
    parser.add_argument('--rpc-port', type=int, default=18457, help='freebankd RPC port')
    parser.add_argument('--rpc-user', required=True, help='RPC username')
    parser.add_argument('--rpc-password', required=True, help='RPC password')
    args = parser.parse_args()

    # Configure handler
    CORSProxyHandler.rpc_url = f'http://{args.rpc_host}:{args.rpc_port}/'
    CORSProxyHandler.rpc_auth = base64.b64encode(
        f'{args.rpc_user}:{args.rpc_password}'.encode()
    ).decode()

    # Start server
    server = HTTPServer(('0.0.0.0', args.port), CORSProxyHandler)
    print(f'CORS Proxy running on http://0.0.0.0:{args.port}')
    print(f'Forwarding to {CORSProxyHandler.rpc_url}')
    print(f'Configure PWA to use: localhost:{args.port}')

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nShutting down...')
        server.shutdown()


if __name__ == '__main__':
    main()
