#!/usr/bin/env python3
# Save as ~/.local/bin/commonlisp-bridge.py

import socket
import sys
import threading
import time
import json
from datetime import datetime

# Log file location
LOG_FILE = "/tmp/commonlisp-bridge.log"

def log(message):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")
        f.flush()

def fix_lsp_response(content):
    """Fix compatibility issues in LSP responses"""
    try:
        data = json.loads(content)

        # Fix initialize response capabilities
        if ("result" in data and
            "capabilities" in data["result"]):

            capabilities = data["result"]["capabilities"]

            # Fix hoverProvider: null -> true
            if "hoverProvider" in capabilities and capabilities["hoverProvider"] is None:
                capabilities["hoverProvider"] = True
                log("Fixed hoverProvider: null -> true")

            # Fix semanticTokensProvider
            if "semanticTokensProvider" in capabilities:
                semantic_tokens = capabilities["semanticTokensProvider"]
                if ("legend" in semantic_tokens and
                    "tokenModifiers" in semantic_tokens["legend"] and
                    semantic_tokens["legend"]["tokenModifiers"] is None):
                    semantic_tokens["legend"]["tokenModifiers"] = []
                    log("Fixed tokenModifiers: null -> []")

        # Fix hover response format
        if ("result" in data and
            data["result"] and
            isinstance(data["result"], dict) and
            "value" in data["result"]):

            # Convert old format to new format
            # Old: {"value": "text"}
            # New: {"contents": {"kind": "plaintext", "value": "text"}}
            old_value = data["result"]["value"]
            data["result"] = {
                "contents": {
                    "kind": "plaintext",
                    "value": old_value
                }
            }
            log("Fixed hover response format: value -> contents")

        return json.dumps(data)
    except Exception as e:
        log(f"Error fixing LSP response: {e}")
        return content

def stdin_to_socket(sock):
    """Read LSP messages from stdin and forward to socket"""
    try:
        log("stdin_to_socket: Starting thread")
        message_count = 0

        while True:
            try:
                # Read Content-Length header
                header = ""
                while not header.endswith("\r\n\r\n"):
                    char = sys.stdin.read(1)
                    if not char:  # EOF
                        log("stdin_to_socket: EOF reached")
                        return
                    header += char

                # Extract content length
                content_length_line = header.split("Content-Length: ")[1].split("\r\n")[0]
                content_length = int(content_length_line)
                log(f"stdin_to_socket: Reading message {message_count}, content length: {content_length}")

                # Read the exact amount of JSON content
                content = sys.stdin.read(content_length)
                if not content:
                    log("stdin_to_socket: No content received")
                    return

                # Parse and log the JSON message
                try:
                    json_data = json.loads(content)
                    method = json_data.get("method", "unknown")
                    msg_id = json_data.get("id", "no-id")

                    # Log extra details for specific methods
                    if method == "textDocument/hover":
                        position = json_data.get("params", {}).get("position", {})
                        uri = json_data.get("params", {}).get("textDocument", {}).get("uri", "unknown")
                        log(f"🔍 HOVER REQUEST: id={msg_id}, uri={uri}, position={position}")
                    elif method == "textDocument/completion":
                        position = json_data.get("params", {}).get("position", {})
                        uri = json_data.get("params", {}).get("textDocument", {}).get("uri", "unknown")
                        log(f"💡 COMPLETION REQUEST: id={msg_id}, uri={uri}, position={position}")
                    else:
                        log(f"📤 REQUEST: method={method}, id={msg_id}")

                except Exception as e:
                    log(f"stdin_to_socket: Message {message_count}: Could not parse JSON: {e}")
                    log(f"stdin_to_socket: Content preview: {content[:100]}...")

                # Send complete message to socket
                message = header + content
                sock.send(message.encode())
                log(f"stdin_to_socket: Forwarded message {message_count} to socket ({len(message)} bytes)")

                message_count += 1

            except Exception as e:
                log(f"stdin_to_socket: Error in message {message_count}: {e}")
                # Try to continue with next message
                continue

    except Exception as e:
        log(f"stdin_to_socket: Fatal error: {e}")
        import traceback
        log(f"stdin_to_socket: Traceback: {traceback.format_exc()}")

def socket_to_stdout(sock):
    """Read LSP messages from socket and forward to stdout"""
    try:
        log("socket_to_stdout: Starting thread")
        message_count = 0

        while True:
            try:
                # Read Content-Length header
                header = b""
                while not header.endswith(b"\r\n\r\n"):
                    char = sock.recv(1)
                    if not char:  # Connection closed
                        log("socket_to_stdout: Connection closed")
                        return
                    header += char

                # Extract content length
                content_length_line = header.decode().split("Content-Length: ")[1].split("\r\n")[0]
                content_length = int(content_length_line)
                log(f"socket_to_stdout: Reading response {message_count}, content length: {content_length}")

                # Read the exact amount of JSON content
                content = b""
                while len(content) < content_length:
                    chunk = sock.recv(content_length - len(content))
                    if not chunk:
                        log("socket_to_stdout: Connection closed while reading content")
                        return
                    content += chunk

                # Log the raw response before fixing
                try:
                    raw_data = json.loads(content.decode())
                    if ("result" in raw_data and
                        raw_data["result"] and
                        isinstance(raw_data["result"], dict)):
                        log(f"🔍 RAW HOVER RESPONSE: {json.dumps(raw_data['result'], indent=2)}")
                except:
                    pass

                # Fix compatibility issues in the response
                fixed_content = fix_lsp_response(content.decode())

                # Parse and log the JSON response
                try:
                    json_data = json.loads(fixed_content)
                    msg_id = json_data.get("id", "no-id")

                    if "result" in json_data:
                        # Check if it's a hover response
                        if json_data["result"] and isinstance(json_data["result"], dict):
                            if "contents" in json_data["result"]:
                                contents = json_data["result"]["contents"]
                                log(f"🔍 HOVER RESPONSE: id={msg_id}, contents: {json.dumps(contents, indent=2)}")
                            elif "items" in json_data["result"]:
                                items = json_data["result"]["items"]
                                log(f"💡 COMPLETION RESPONSE: id={msg_id}, {len(items)} items")
                            else:
                                log(f"📥 RESPONSE: id={msg_id}, result keys: {list(json_data['result'].keys())}")
                        else:
                            log(f"📥 RESPONSE: id={msg_id}, result={json_data['result']}")
                    elif "error" in json_data:
                        log(f"❌ ERROR RESPONSE: id={msg_id}, error={json_data['error']}")
                    else:
                        log(f"📥 OTHER RESPONSE: id={msg_id}")

                except Exception as e:
                    log(f"socket_to_stdout: Response {message_count}: Could not parse JSON: {e}")
                    log(f"socket_to_stdout: Content preview: {fixed_content[:100]}...")

                # Send complete message to stdout with fixed content
                fixed_content_bytes = fixed_content.encode()
                new_header = f"Content-Length: {len(fixed_content_bytes)}\r\n\r\n"
                message = new_header.encode() + fixed_content_bytes

                sys.stdout.buffer.write(message)
                sys.stdout.buffer.flush()
                log(f"socket_to_stdout: Forwarded response {message_count} to stdout ({len(message)} bytes)")

                message_count += 1

            except Exception as e:
                log(f"socket_to_stdout: Error in response {message_count}: {e}")
                # Try to continue with next message
                continue

    except Exception as e:
        log(f"socket_to_stdout: Fatal error: {e}")
        import traceback
        log(f"socket_to_stdout: Traceback: {traceback.format_exc()}")

def main():
    # Clear log file and start logging
    with open(LOG_FILE, "w") as f:
        f.write("")

    log("=== Common Lisp Bridge Starting ===")
    log(f"Args: {sys.argv}")

    # Connect to alive-lsp
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        log("Attempting to connect to alive-lsp on port 9001...")
        sock.connect(('localhost', 9001))
        log("Successfully connected to alive-lsp on port 9001")
    except Exception as e:
        log(f"Error: Could not connect to alive-lsp on port 9001: {e}")
        sys.exit(1)

    # Start forwarding threads
    log("Starting forwarding threads...")
    stdin_thread = threading.Thread(target=stdin_to_socket, args=(sock,), daemon=True)
    stdout_thread = threading.Thread(target=socket_to_stdout, args=(sock,), daemon=True)

    stdin_thread.start()
    stdout_thread.start()
    log("Forwarding threads started")

    try:
        # Wait for threads to finish
        log("Waiting for threads to finish...")
        stdin_thread.join()
        stdout_thread.join()
        log("Threads finished")
    except KeyboardInterrupt:
        log("Bridge interrupted by user")
    except Exception as e:
        log(f"Bridge error: {e}")
    finally:
        sock.close()
        log("Socket closed, bridge ending")

if __name__ == "__main__":
    main()
