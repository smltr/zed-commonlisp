#!/usr/bin/env python3
# Save as dev/test_hover.py

import socket
import json
import time

def send_request(sock, method, params, request_id=None):
    request = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params
    }
    if request_id is not None:
        request["id"] = request_id

    content = json.dumps(request)
    message = f"Content-Length: {len(content)}\r\n\r\n{content}"

    print(f"Sending: {method}")
    sock.send(message.encode())

def read_response(sock):
    # Read Content-Length header
    header = b""
    while not header.endswith(b"\r\n\r\n"):
        header += sock.recv(1)

    # Get content length
    content_length = int(header.decode().split("Content-Length: ")[1].split("\r\n")[0])

    # Read JSON content
    content = b""
    while len(content) < content_length:
        content += sock.recv(content_length - len(content))

    return json.loads(content.decode())

# Connect to alive-lsp
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('localhost', 9001))

try:
    # Initialize
    send_request(sock, "initialize", {
        "processId": None,
        "rootUri": "file:///tmp",
        "capabilities": {
            "textDocument": {
                "hover": {"contentFormat": ["markdown", "plaintext"]}
            }
        }
    }, 1)

    response = read_response(sock)
    print("✅ Initialize successful")
    print(f"Hover capability: {response.get('result', {}).get('capabilities', {}).get('hoverProvider')}")

    # Initialized notification
    send_request(sock, "initialized", {})

    # Open document
    send_request(sock, "textDocument/didOpen", {
        "textDocument": {
            "uri": "file:///tmp/test.lisp",
            "languageId": "commonlisp",
            "version": 1,
            "text": "(defun hello-world () 'hello)"
        }
    })

    time.sleep(0.5)

    # Request hover on "defun"
    send_request(sock, "textDocument/hover", {
        "textDocument": {"uri": "file:///tmp/test.lisp"},
        "position": {"line": 0, "character": 2}  # Position on "defun"
    }, 2)

    response = read_response(sock)
    print("✅ Hover response received")
    print(f"Hover result: {response.get('result')}")

finally:
    sock.close()
