import sys
#allows input from the command line
import socket 
#allows http comunocation 
import ssl
#for timeouts
import time
from dataclasses import dataclass

last_redirect = ""

class Response:
    response_header: str
    password_protected: int #0 if no, 1 if yes
    website: str

    def __init__(self, rsp, pass_p, web):
        self.response_header = rsp
        self.password_protected = pass_p
        self.website = web

class Cookie:
    name: str
    domain: str = ""
    expires: str = ""

    def __init__(self, myname: str):
        self.name = "cookie name: " + myname

    def add_domain(self, domain: str):
        self.domain = ", domain name: " + domain

    def add_expires(self, expires: str):
        self.expires = ", expires time: " + expires

    def __repr__(self):
        return self.name + self.expires + self.domain

class HostClass:
    scheme: str = ""
    netloc: str = ""
    rest: str = ""
    uri: str = ""
    port: int = 80

    def __init__(self, inp: str):
        #seperate the scheme
        parts1 = inp.split("://")
        #seperate the netloc from the rest of the uri and set it
        if(len(parts1) > 1):
            parts2 = parts1[1].split("/")
            #add the rest of the uri to the obj
            count = 1
            while count < len(parts2):
                self.rest += "/"
                self.rest += parts2[count]
                count += 1
        else:
            parts2 = inp.split("/")
            #add the rest of the uri to the obj
            count = 1
            while count < len(parts2):
                self.rest += "/"
                self.rest += parts2[count]
                count += 1
        self.netloc = parts2[0]
        #check if scheme is in the uri and check if its http or https
        if parts1[0] == "https":
            self.scheme = "https"
            self.uri = inp    
            self.port = 443
        elif parts1[0] == "http":
            self.scheme = "http"
            self.uri = inp
        else:
            self.scheme = "https"
            self.uri = self.scheme + "://" + inp
            self.port = 443
        #chek if rest is still empty
        if len(self.rest) <= 0:
            self.rest = "/"

        #for testing
        #print("uri:",self.uri,"scheme:", self.scheme,"hostname:" ,self.netloc,"rest:", self.rest)

    def add_location(self,rest: str):
        self.uri += rest
        self.rest = self.rest[:-1]
        self.rest += rest

def main() -> None:
    """
    In: Domain name
    """
    #call get uri to get the uri
    host = get_uri()

    #call http_connect to run through the http connection
    response, new_host = http_connect(host)

    #call get_cookies to get the cookies
    cookies = get_cookies(response.response_header)

    #Check HTTP 2
    http2 = check_http2(new_host)

    #print final output
    print_output(response,cookies,http2)

    #return
    return None

def get_uri() -> HostClass:
    """
    In: void
    Out: A HostClass obj
    Def: This fuction will read the URI from
    the command line and return it as a string
    """
    try: #Check if too many arguments were passed
        str(sys.argv[2])
        print("Error: Too Many arguments")
        exit()
    except IndexError:
        try:
            host = HostClass(str(sys.argv[1]))

            return host
        except IndexError: #Check if no argument was passed
            print("Error: No Domain Name Given")
            exit()

def http_connect(host: HostClass) -> Response:
    """
    In: host: HostClass
    Out: http response header
    Def: This Function is designed to call the other http related functions and 
    be called recursively
    """

    #create a default context
    context = ssl.create_default_context()

    #call init_connection to initialize the connection and get our SSL Socket
    conn = init_connection(host, context)

    #call send_rqst to send a request
    send_rqst(conn, host)

    #call receive_rsp to receive a response
    response, good_host = receive_rsp(conn, host)

    #close connection\
    conn.close()

    return response, good_host

def init_connection(host: HostClass, context: ssl):
    """
    In: host: HostClass obj
    Out: SSL socket
    Def: initialize the wrapped socket and makes a connection
    """
    try:
        try:
            if host.port == 443:
                conn = context.wrap_socket(socket.socket(socket.AF_INET), server_hostname= host.netloc)
            else:
                conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #make a connection
            conn.connect((host.netloc, host.port))
            return conn
        #In case of no connection
        except OSError:
            print("\nUnable to Connect to the given URL\n\nCheck the spelling of your URL and your internet connection then try again")
            exit()
    except socket.gaierror:
        print("\nUnable to Connect to the given URL\n\nCheck the spelling of your URL and your internet connection then try again")
        exit()

def send_rqst(conn, host: HostClass) -> None:
    """
    In: conn: SSL socket, host: HostClass obj
    Out: void
    Def: This function send a request to the currently connected server
    """
    print("---Request begin---")#for clarity
    #write the http request
    http_request = "GET {} HTTP/1.1\r\nHost: {}\r\nConnection: Keep-Alive\r\n\r\n".format(host.rest, host.netloc)
    print(http_request.strip(), "\n") #for clarity
    #send the http request
    conn.send(http_request.encode())
    #print("---Request begin---\nGET",uri)
    print("---Request end---\nHTTP request sent, Port {}, awaiting response...\n".format(host.port))
    return None

def receive_rsp(conn, host: HostClass):
    """
    In: void
    Out: Response Header and (0 - if no password or 1 if password protected)
    Def: This fuction receives the response and returns it as a string
    """
    #define response variable
    response = b""
    #set start time
    start_time = time.time()
    #set a socket timeout
    conn.settimeout(3)
    #initialize header and body variblers
    response_header = ""
    response_body = ""
    #initialize password protected variable
    pass_p = 0
    body = 1
    try:
        #read the header, and add it to response_header
        data = conn.recv(1024)
        response_header += data.decode('utf-8',errors="ignore")
        #check the code
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    body = 0
                    break  
                if data.decode('utf-8',errors="ignore") == "":
                    body = 0
                    break  
                #check if the header is over
                s_data = data.decode('utf-8',errors="ignore").split("\n<")
                if s_data[0][0] == "<":
                    response_body += data.decode('utf-8',errors="ignore")
                    break
                else:
                    #double check if the header is over
                    if len(s_data) > 1 :
                        response_header += s_data[0]
                        response_body += "<"
                        i = 1
                        while len(s_data) > i:
                            response_body += s_data[i]
                            i += 1
                        break
                #check for a decoding error
            except UnicodeDecodeError:
                response_body += "This Line could not be decoded"
        if body == 1:
            while True:
                try:
                    #print the body
                    data = conn.recv(1024)
                    if not data:
                        break   
                    response_body += data.decode('utf-8',errors="ignore")
                except UnicodeDecodeError:
                    response_body += "This Line could not be decoded"
        else:
            response_body = "No response body"
    #check timeout
    except socket.timeout:
        response_body +=""

    code = check_header(response_header)
    if code == 4:
        pass_p = 1
    elif code == 3:
        #recursively call to redirected url
        redirect = find_redirect(response_header)
        if redirect == "0":
            None
        elif "http" not in redirect:
            conn.close()
            host.add_location(redirect)
            return http_connect(host)
        else:
            conn.close()
            host1 = HostClass(str(redirect))
            return http_connect(host1)
        
    #print response for clarity
    print("---Response header---")
    print(response_header)
    #print("---Response body---")
    #print(response_body)
    

    #return response header
    return Response(response_header, pass_p, host.netloc), host

def check_header(rsp: str) -> int:
    """
    In: An http response header \n
    Out: \n 
    if code is 2** -> 2 \n
    if code is 3** -> 3 \n
    if code is 401 -> 4 \n
    Def: check_header checks the response code and returns accordingly
    """
    #get line of code from HTTP request
    lines = rsp.split('\n')
    code = lines[0].split(" ")[1]

    #print(code+"\n\n\n\n\n\n\n")#for test

    #return correct response
    if code == "401":
        #print("\n\n\n\n\n\n\n\nSUCESS IN CHECK_HEADER 401\n\n\n\n\n")#for test
        return 4
    elif code[0] == "2":
        #print("\n\n\n\n\n\n\n\nSUCESS IN CHECK_HEADER 2***\n\n\n\n\n")#for test
        return 2
    elif code[0] == "3":
        return 3
    elif code[0] == "1":
        print("ERROR: Informational Response; Code: " + code)
        exit()
    elif code[0] == "4":
        print("ERROR: Client Error Response; Code: " + code)
        exit()
    elif code[0] == "5":
        print("ERROR: Server Error Response; Code: " + code)
        exit()

def find_redirect(rsp:str) -> str:
    """
    In: http response header
    Out: redirect url
    Def: given a http response header, this function finds and returns the redirect URL
    """
    #print that a redirect is happening
    print("Redirect code found, Attempting Redirect...\n")
    #define a variable for uri
    uri = ""
    #split each line seperately
    lines = rsp.split("\n")
    #loop through all lines
    for line in lines:
        if line.startswith("Location:"):
            uri = line.split("n: ")[1].strip()
        if line.startswith("location:"):
            uri = line.split("n: ")[1].strip()
            
    #check if url was found
    if uri == "":
        print("ERROR: No valid redirect URL given, Printing initial response...\n")
        return "0"
    #check if url was the same as the last redirect
    global last_redirect
    if uri == last_redirect :
        print("ERROR: Repeat redirect URL, Printing response...\n")
        return "0"
    else:
        last_redirect = uri
    return uri

def get_cookies(rsp: str)-> list:
    """
    In: http response
    Out: list of cookies obj
    Def: This program receives an http response and parses it for cookies
    """

    #create a list for storing each cookie obj
    cookies = []
    #split each line seperately
    lines = rsp.split('\n')

    #loop through all lines
    for line in lines:
        if line.startswith("Set-Cookie:"):

            #get cookie name and initialize a cookie object
            cookie_parts = line.split(';')
            cookie = Cookie(cookie_parts[0].split('=')[0].strip())
            #add the cookie to the list
            cookies.append(cookie)
           
            
            #loop to get the rest 
            for part in cookie_parts[1:]:
                if part.startswith(" domain"):
                    #add domain to cookie obj
                    cookie.add_domain(part.split('=')[1].strip())
                elif part.startswith(" expires"):
                    #add expires to cookie obj
                    cookie.add_expires(part.split('=')[1].strip())
        elif line.startswith("set-cookie:"):

            #get cookie name and initialize a cookie object
            cookie_parts = line.split(';')
            cookie = Cookie(cookie_parts[0].split('=')[0].strip())
            #add the cookie to the list
            cookies.append(cookie)
           
            
            #loop to get the rest 
            for part in cookie_parts[1:]:
                if part.startswith(" domain"):
                    #add domain to cookie obj
                    cookie.add_domain(part.split('=')[1].strip())
                elif part.startswith(" expires"):
                    #add expires to cookie obj
                    cookie.add_expires(part.split('=')[1].strip())

    return cookies

def check_http2(host:HostClass)-> int:
    """
    return False if no
    return True if yes
    """
    try:
        try:
            #https
            if host.port == 443:
                #creat a connection
                context = ssl.create_default_context()
                context.set_alpn_protocols(['http/1.1', 'h2'])
                conn = context.wrap_socket(socket.socket(socket.AF_INET), server_hostname= host.netloc)
                conn.connect((host.netloc, 443))
                if 'h2' == conn.selected_alpn_protocol():
                    return True
                else:
                    return False
                

            #http
            else:
                conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                #make a connection
                conn.connect((host.netloc, host.port))
                #write the http request
                http_request = "GET {} HTTP/1.1\r\nHost: {}\r\nUprgrade: h2c\r\nConnection: Uprgrade\r\n\r\n".format(host.rest, host.netloc)
                #send the http request
                conn.send(http_request.encode())
                response = b''
                chunk = conn.recv(1024)
                response += chunk
                conn.close()
                return b'HTTP/2' in response
                
        #In case of no connection
        except OSError:
            print("\nUnable to Connect to the given URL\n\nCheck the spelling of your URL and your internet connection then try again")
            return False
    except socket.gaierror:
        print("\nUnable to Connect to the given URL\n\nCheck the spelling of your URL and your internet connection then try again")
        return False
        
        


def print_output(rsp: Response, cookies:list, http2: int) -> None:
    """
    In: Response, Cookies, HTTP2[y/n] - 1 if yes 0 if no
    Out: Void
    Def: This Function prints the required output of the assignment
    including: supports http2(y/n), list of cookies, password protected(y/n)
    """
    #print website
    print("\n\nwebsite: " + rsp.website)
    #print http compatibility
    if http2 == False:
        print("1. Supports http2: no")
    elif http2 == True:
        print("1. Supports http2: yes")
    else:
        print("Invalid parameter passed to http2")
    #print cookies
    print("2. List of Cookies:")
    if len(cookies) == 0:
        print("No Cookies Found")
    else:
        for cookie in cookies:
            print(cookie)
    #print Password protected
    if rsp.password_protected == 0:
        print("3. Password-protected: no")
    elif rsp.password_protected == 1:
        print("3. Password-protected: yes") 
    else:
        print("Invalid parameter passed to password protected")
    return None

main()

