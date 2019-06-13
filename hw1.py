"""
Jose E. Rodriguez
CS 450 Fall 2018
Programming Assignment 1
University of Illinois at Chicago

This is a bare bones HTTP 1.1 client which really only implements:
Include a 'host' header.
Correctly interpret Transfer-encoding: chunked.
Include a Connection: close header, or handle persistent connections.

USAGE: command line, arg 1 is URL.
Example: python3 hw1.py http://www.example.com
"""

import logging
import socket
import sys


def transfer_chunk_encoding(message_body):
    """
    Handle Transfer Chunk Encoding by parsing in pairs.
    The first item being what determines the size of the
    chunk and the second item being the chunk itself.
    """
    body_content = b''
    escape = bytes(b'0')

    while True:
        # Slice the message body to get hex line
        crlf_index = message_body.find(b'\r\n')
        hex_bytes = message_body[:crlf_index]

        # Does hex line have semi colon + params?
        hex_sc_index = hex_bytes.find(b';')
        if hex_sc_index != -1:
            hex_bytes = hex_bytes[:hex_sc_index]

        # Convert hex number to decimal
        hex_amount = int(hex_bytes.decode(), 16)
        message_body = message_body[crlf_index+2:]

        # Slice AGAIN to get chunk of data
        data = message_body[:hex_amount]

        # Get new msg body (Skip trailing CRLF)
        message_body = message_body[hex_amount+2:]

        # Is the current line the end?
        if hex_bytes == escape:
            break

        # Accumulate data to new body
        body_content += data

    return body_content


def find_port(host):
    """
    Determine what the URL's port number is
    and return that port number along with the
    host name.
    """

    # Non standard port?
    diff_port = host.find(":")
    port = 80

    if diff_port != -1:
        port = host[diff_port+1:]
        host = host[:diff_port]

    return host, port


def parse_url(url):
    """
    Parse the url into the Host and path.
    Path cannot be empty, returns '/' instead.
    """
    # append a '/' to URL
    url += "/"

    # split and print parts or URL
    first, sec, host, path = url.split("/", 3)

    # Is PATH empty?
    if not path:
        path = "/"          # set path to root directory
    else:
        path = "/" + path   # prepend '/'
        path = path[:-1]    # remove the originally appended '/'

    return host, path       # return the host and path names


def retrieve_url(url):
    """
    retrieve_url: Takes a url (as a str) as its only argument, and
    uses the HTTP protocol to retrieve and return the body's bytes.
    Return bytes of the body of the document at url.
    """
    # Create the HTTP message to send through the socket
    host, path = parse_url(url)
    host, port = find_port(host)
    request_line = "GET " + path + " HTTP/1.1\r\n"   # Tells server what to do
    host_header = "Host: " + host + "\r\n"           # Only required header
    conn_header = "Connection: close\r\n"            # Close connection
    message_end = "\r\n"                             # End on a CRLF

    # Encode the HTTP message into bytes to be sent via socket
    http_message = str.encode(request_line + host_header + conn_header + message_end)

    # Initiate a connection with sockets
    sock = socket.create_connection((host, port))

    # Send the HTTP message!
    sock.sendall(http_message)

    # Receive the HTTP response via socket
    data = b''                        # Holds entire HTTP response
    while True:
        data_buffer = sock.recv(1024)    # Get the next chunk of data

        if not data_buffer:
            break
        else:
            data += data_buffer

    # Close the socket connection
    sock.close()

    # Find the two CRLFs amongst the data
    data = bytearray(data)

    # Slice status line
    stat_line_index = data.find(b"\r\n")
    status_line = bytearray(data[:stat_line_index])

    # Check status code
    status_ok = status_line.find(b'200')
    if status_ok == -1:
        return None

    # Slice list to get message header
    crlf_index = data.find(b"\r\n\r\n")
    message_header = data[:crlf_index]

    # Slice list to get body
    body_begin = crlf_index + 4
    message_body = bytes(data[body_begin:])

    # Transfer-chunk encoding?
    tr_chunked = message_header.find(b"Transfer-Encoding: chunked")

    if tr_chunked != -1:
        message_body = transfer_chunk_encoding(message_body)

    return message_body


if __name__ == "__main__":
    sys.stdout.buffer.write(retrieve_url(sys.argv[1]))  # pylint: disable=no-member
