#!/usr/bin/env python3
# Save as dev/test_simple.py

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
sock.connect(('localhost', 9000))

try:
    # 1. Initialize
    send_request(sock, "initialize", {
        "processId": None,
        "rootUri": "file:///tmp",
        "capabilities": {
            "textDocument": {
                "completion": {"completionItem": {"snippetSupport": True}}
            }
        }
    }, 1)

    response = read_response(sock)
    print("✅ Initialize successful")

    # 2. Initialized notification
    send_request(sock, "initialized", {})

    # 3. Open document
    send_request(sock, "textDocument/didOpen", {
        "textDocument": {
            "uri": "file:///tmp/test.lisp",
            "languageId": "commonlisp",
            "version": 1,
            "text": "(def"
        }
    })

    # 4. Request completion
    send_request(sock, "textDocument/completion", {
        "textDocument": {"uri": "file:///tmp/test.lisp"},
        "position": {"line": 0, "character": 4}
    }, 2)

    response = read_response(sock)
    print("✅ Completion response received")

    if response.get('result') and response['result'].get('items'):
        items = response['result']['items']
        print(f"Found {len(items)} completions:")
        for i, item in enumerate(items[:10]):
            print(f"  {i+1}. {item['label']}")
    else:
        print("No completions found")

finally:
    sock.close()
