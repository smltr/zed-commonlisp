#!/usr/bin/env python3
# Save as dev/test_bridge.py

import subprocess
import json
import time

def send_request(process, method, params, request_id=None):
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
    process.stdin.write(message.encode())
    process.stdin.flush()

def read_response(process):
    # Read Content-Length header
    header = b""
    while not header.endswith(b"\r\n\r\n"):
        header += process.stdout.read(1)

    # Get content length
    content_length = int(header.decode().split("Content-Length: ")[1].split("\r\n")[0])

    # Read JSON content
    content = process.stdout.read(content_length)

    return json.loads(content.decode())

# Start the bridge
process = subprocess.Popen(
    ["python3", "dev/bridge.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

try:
    # Test the same sequence as before
    send_request(process, "initialize", {
        "processId": None,
        "rootUri": "file:///tmp",
        "capabilities": {
            "textDocument": {
                "completion": {"completionItem": {"snippetSupport": True}}
            }
        }
    }, 1)

    response = read_response(process)
    print("✅ Initialize successful")

    send_request(process, "initialized", {})

    send_request(process, "textDocument/didOpen", {
        "textDocument": {
            "uri": "file:///tmp/test.lisp",
            "languageId": "commonlisp",
            "version": 1,
            "text": "(def"
        }
    })

    send_request(process, "textDocument/completion", {
        "textDocument": {"uri": "file:///tmp/test.lisp"},
        "position": {"line": 0, "character": 4}
    }, 2)

    response = read_response(process)
    print("✅ Completion response received")

    if response.get('result') and response['result'].get('items'):
        items = response['result']['items']
        print(f"Found {len(items)} completions:")
        for i, item in enumerate(items[:10]):
            print(f"  {i+1}. {item['label']}")
    else:
        print("No completions found")

finally:
    process.terminate()
