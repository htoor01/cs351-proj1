"""CS 352 Project 1 - client.

Usage: python3 client.py [server-host] [port]
Defaults: server-host = localhost, port = 30083

Reads in-proj.txt one line at a time, sends each line to the server as
    <line-number>|<message>\n
validates each response record
    <line-number>|<message-length>|<transformed-message>\n
and writes the validated records (or ERROR records) to out-proj.txt.
"""

import socket
import sys


ASSIGNED_PORT = 30083
DEFAULT_SERVER_HOST = "localhost"
INPUT_FILE = "in-proj.txt"
OUTPUT_FILE = "out-proj.txt"


class RecordReader:
    """Splits a TCP byte stream into newline-terminated records."""

    def __init__(self, sock):
        self.sock = sock
        self.buffer = b""

    def next_record(self):
        """Return the next record (without the newline), or None at end of stream."""
        while b"\n" not in self.buffer:
            data = self.sock.recv(4096)
            if not data:
                return None
            self.buffer += data
        record, self.buffer = self.buffer.split(b"\n", 1)
        return record


def validate(line_number, record):
    """Return the output record to write for one server response."""
    text = record.decode("utf-8", errors="replace")
    parts = text.split("|", 2)
    if len(parts) != 3:
        print(f"[C]: ERROR line {line_number}: malformed response {text!r}")
        return f"{line_number}|ERROR|reported-length=MISSING|actual-length=MISSING"

    returned_line, reported_length, transformed = parts
    actual_length = len(transformed.encode("utf-8"))

    line_ok = returned_line == str(line_number)
    length_ok = reported_length == str(actual_length)
    if line_ok and length_ok:
        return f"{returned_line}|{reported_length}|{transformed}"

    if not line_ok:
        print(f"[C]: ERROR line {line_number}: server returned line number "
              f"{returned_line!r}")
    if not length_ok:
        print(f"[C]: ERROR line {line_number}: reported length {reported_length}, "
              f"actual length {actual_length}")
    return (f"{line_number}|ERROR|reported-length={reported_length}"
            f"|actual-length={actual_length}")


def client(server_host, port):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("[C]: Client socket created")
    except OSError as err:
        print(f"[C]: Socket open error: {err}")
        return

    try:
        client_socket.connect((server_host, port))
        print(f"[C]: Connected to {server_host}:{port}")
        reader = RecordReader(client_socket)

        with open(INPUT_FILE, "r", encoding="utf-8") as infile, \
                open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:
            for line_number, line in enumerate(infile, start=1):
                message = line.rstrip("\r\n")
                request = f"{line_number}|{message}\n"
                client_socket.sendall(request.encode("utf-8"))
                print(f"[C]: Sent: {message!r}")

                record = reader.next_record()
                if record is None:
                    print("[C]: Server closed the connection early")
                    break
                print(f"[C]: Received: {record.decode('utf-8', errors='replace')!r}")
                outfile.write(validate(line_number, record) + "\n")

        # Tell the server we are done sending so it can finish.
        client_socket.shutdown(socket.SHUT_WR)
    except OSError as err:
        print(f"[C]: Client error: {err}")
    finally:
        client_socket.close()


if __name__ == "__main__":
    if len(sys.argv) > 3:
        print("Usage: python3 client.py [server-host] [port]")
        sys.exit(1)
    host = sys.argv[1] if len(sys.argv) >= 2 else DEFAULT_SERVER_HOST
    port = int(sys.argv[2]) if len(sys.argv) == 3 else ASSIGNED_PORT
    client(host, port)
    print("Done.")
