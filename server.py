"""CS 352 Project 1 - server.

Usage: python3 server.py [port]

Accepts one TCP connection and answers every request record
    <line-number>|<message>\n
with a response record
    <line-number>|<message-length>|<transformed-message>\n
where the transformed message is the reversed, case-swapped message.
With 10% probability the reported length is deliberately wrong.
"""

import random
import socket
import sys


ASSIGNED_PORT = 30083
# Bind to all interfaces so clients on other ilab machines can connect.
BIND_HOST = ""


def transform(message):
    return message[::-1].swapcase()


def build_response(record):
    """Return the response bytes for one request record, or None if malformed."""
    try:
        text = record.decode("utf-8")
    except UnicodeDecodeError:
        print(f"[S]: Malformed request (not UTF-8): {record!r}")
        return None

    parts = text.split("|", 1)
    if len(parts) != 2:
        print(f"[S]: Malformed request (missing '|'): {text!r}")
        return None

    line_field, message = parts
    try:
        line_number = int(line_field)
    except ValueError:
        print(f"[S]: Malformed request (bad line number): {text!r}")
        return None

    transformed = transform(message)
    actual_length = len(transformed.encode("utf-8"))
    if random.random() < 0.10:
        reported_length = actual_length + random.randint(1, 1000)
        print(f"[S]: Injecting length fault on line {line_number}: "
              f"reported {reported_length}, actual {actual_length}")
    else:
        reported_length = actual_length

    print(f"[S]: Received: {message!r} -> sending: {transformed!r}")
    response = f"{line_number}|{reported_length}|{transformed}\n"
    return response.encode("utf-8")


def serve_client(client_socket):
    buffer = b""
    while True:
        data = client_socket.recv(4096)
        if not data:
            break
        buffer += data
        # Process every complete record; keep any partial record buffered.
        while b"\n" in buffer:
            record, buffer = buffer.split(b"\n", 1)
            response = build_response(record)
            if response is not None:
                client_socket.sendall(response)

    if buffer:
        print(f"[S]: Discarding incomplete record at end of stream: {buffer!r}")


def server(port):
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print("[S]: Server socket created")
    except OSError as err:
        print(f"[S]: Socket open error: {err}")
        return

    try:
        server_socket.bind((BIND_HOST, port))
        server_socket.listen(1)
        print(f"[S]: Server host name is {socket.gethostname()}")
        print(f"[S]: Server port is {port}")

        client_socket, client_address = server_socket.accept()
        print(f"[S]: Got a connection request from a client at {client_address}")
        with client_socket:
            serve_client(client_socket)
        print("[S]: Client closed the connection")
    except OSError as err:
        print(f"[S]: Server error: {err}")
    finally:
        server_socket.close()


if __name__ == "__main__":
    if len(sys.argv) > 2:
        print("Usage: python3 server.py [port]")
        sys.exit(1)
    port = int(sys.argv[1]) if len(sys.argv) == 2 else ASSIGNED_PORT
    server(port)
    print("Done.")
