import socket
import traceback
from datetime import date

def get_requested_method(request_line):
    parts = request_line.split()
    request_method = parts[0]
    return request_method

def get_requested_filename(request_line):
    parts = request_line.split()
    path = parts[1]
    if not path.startswith("."):
        return "." + path
    return path

def get_file_type(file_name):
    return "." + file_name.split(".")[-1]

def get_content_type(file_extension):
    if file_extension == ".html" or file_extension == ".htm":
        return "text/html; charset=utf-8"
    elif file_extension == ".txt":
        return "text/plain; charset=utf-8"
    elif file_extension == ".jpg" or file_extension == ".jpeg":
        return "image/jpeg"
    elif file_extension == ".png":
        return "image/png"
    elif file_extension == ".css":
        return "text/css; charset=utf-8"
    elif file_extension == ".ico":
        return "image/x-icon"
    elif file_extension == ".js":
        return "text/javascript; charset=utf-8"
    else:
        return "application/octet-stream"

# This function (and the following) was moved here for clarity,
# but is the same thing we have done in the
# past to handle special routes like /shutdown and getting request bodies
def handle_special_routes(requested_filename, connection_to_browser):
    if requested_filename == "./shutdown":
        print("Server shutting down")
        shutdown_connection(connection_to_browser)
        exit()

def get_file_body_in_bytes(requested_filename):
    with open(requested_filename, "rb") as fd:
        return fd.read()
    
def get_secret_file_body_in_bytes(requested_filename, username):
    with open(requested_filename, "rb") as fd:
        html_contents = fd.read().decode("utf-8")
    todayDate = date.today().strftime(("%Y-%m-%d"))
    response_body = html_contents.format(username=username, date=todayDate)
    return response_body.encode("utf-8")

def parse_headers(reader_from_browser):
    headers = {}
    header_line = reader_from_browser.readline().decode("utf-8")
    while(True):
        if header_line == "\r\n":
            break
        pair = header_line.split(": ")
        headers[pair[0]] = pair[1].strip()
        header_line = reader_from_browser.readline().decode("utf-8")
    return headers

def parse_post_request_form_fields(headers, reader_from_browser):
    content_length = int(headers["Content-Length"])
    content_type = headers["Content-Type"]
    post_body = reader_from_browser.read(content_length)
    print("Raw POST Body: ", post_body)
    post_body = post_body.decode("utf-8")
    form_fields = {}
    if content_type == "text/plain":
        post_lines = post_body.split("\r\n")
        for line in post_lines:
            if line == '':
                break
            pair = line.split("=")
            form_fields[pair[0]] = pair[1]
    elif content_type == "application/x-www-form-urlencoded":
        post_lines = post_body.split("&")
        for line in post_lines:
            if line == '':
                break
            pair = line.split("=")
            form_fields[pair[0]] = pair[1]
    return form_fields

def main(testing_flags=None):
    # Do not change the following code. This is here to allow us to manage part of your server
    # during testing.
    flags = initialize_flags(testing_flags)

    server = create_connection(port = 8080)

    while flags["continue"]:
        # Wait for the browser to send a HTTP Request
        connection_to_browser = accept_browser_connection_to(server)

        # Read the HTTP Request from the browser
        reader_from_browser = connection_to_browser.makefile(mode='rb')
        try:
            request_line = reader_from_browser.readline().decode("utf-8") # decode converts from bytes to text
            print()
            print('Request:')
            print(request_line)
        except Exception as e:
            print("Error while reading HTTP Request:", e)
            traceback.print_exc() # Print what line the server crashed on.
            shutdown_connection(connection_to_browser)
            continue

        # Gets the requested filename, extension, and file type
        requested_filename = get_requested_filename(request_line)
        file_extension = get_file_type(requested_filename)
        content_type = get_content_type(file_extension)

        # Done: Get the requested HTTP Method
        # Implement a new get_requested_method function, which takes the
        # request line, and then call it here
        request_method = get_requested_method(request_line)

        # Done: Print requested method
        print("Request method: ", request_method)
        print("Requested file:", requested_filename)
        print("Extension:", file_extension)

        # TODO: Read all Headers into a Dictionary
        # Implement a new parse_headers function, which takes the
        # browser stream (called reader_from_browser),
        # and then call it here
        headers = parse_headers(reader_from_browser)

        # Move handling shutdown to a new function for clarity
        handle_special_routes(requested_filename, connection_to_browser)

        # Write the HTTP Response back to the browser
        writer_to_browser = connection_to_browser.makefile(mode='wb')
        try:
            # TODO: Handle GET and POST requests differently
            # The code below is what we did before to handle GET requests,
            # but it's been partially moved into a function for clarity.
            if request_method == "GET":
                response_body = get_file_body_in_bytes(requested_filename)
            else:
                # POST
                post_form_fields = parse_post_request_form_fields(headers, reader_from_browser)
                if requested_filename == "./hello.html":
                    if post_form_fields["secret_passcode"] == "abc123":
                        # load secret
                        username = post_form_fields["username"]
                        response_body = get_secret_file_body_in_bytes("./secret.html", username)
                    else:
                        # load hello.html
                        response_body = get_file_body_in_bytes("./hello.html")
                else:
                    # what do?
                    response_body = get_file_body_in_bytes(requested_filename)


            # TODO: Implement a new function called parse_post_request_form_fields.
            # It should have the following signature:
            #   parse_post_request_form_fields(headers, reader_from_browser)
            #
            # It should return a dictionary of the form fields and their values.
            # Then, call the parse_post_request_form_fields function here to get the
            # form field values.
            # Then print the fields for debugging.

            # TODO: Decide what to do with the data.

            response_headers = "\r\n".join([
                'HTTP/1.1 200 OK',
                f'Content-Type: {content_type}',
                f'Content-length: {len(response_body)}',
                'Connection: close',
                '\r\n'
            ]).encode("utf-8")

            # These lines just PRINT the HTTP Response to your Terminal.
            print()
            print('Response headers:')
            print(response_headers)
            print()
            print('Response body:')
            print(response_body)
            print()

            # These lines do the real work; they write the HTTP Response to the Browser.
            writer_to_browser.write(response_headers)
            writer_to_browser.write(response_body)
            writer_to_browser.flush()
        except Exception as e:
            print("Error while writing HTTP Response:", e)
            flags["exceptions"].append(e)
            traceback.print_exc() # print what line the server crashed on
    
        shutdown_connection(connection_to_browser)



# Don't worry about the details of the rest of the code below.
# It is VERY low-level code for creating the underlying connection to the browser.

def create_connection(port):
    addr = ("", port)  # "" = all network adapters; usually what you want.
    server = socket.create_server(addr, family=socket.AF_INET6, dualstack_ipv6=True) # prevent rare IPV6 softlock on localhost connections
    server.settimeout(2)
    print(f'Server started on port {port}. Try: http://localhost:{port}/form.html')
    return server

def accept_browser_connection_to(server):
    while True:
        try:
            (conn, address) = server.accept()
            conn.settimeout(2)
            return conn
        except socket.timeout:
            print(".", end="", flush=True)
        except KeyboardInterrupt:
            exit(0)

def shutdown_connection(connection_to_browser):
    connection_to_browser.shutdown(socket.SHUT_RDWR)
    connection_to_browser.close()

def initialize_flags(testing_flags):
    flags = testing_flags if testing_flags is not None else {}
    if "continue" not in flags:
        flags["continue"] = True
    if "exceptions" not in flags:
        flags["exceptions"] = []
    return flags

if __name__ == "__main__":
    main()
