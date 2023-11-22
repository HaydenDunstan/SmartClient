# SmartClient
A basic web client designed as a project for a university assignment in a third year Computer Networks course

The Program will:
1. Send a HTTP get request to your chosen url
2. Redirect as required
3. Print the response header
4. Print whether the website supports HTTP2, the cookies the website uses, and whether the website is password protected

The program will default to https, port 443 if unspecified, but can also use http, port 80

Code will commpile automatically
To run the code input one of the following lines and replace [URL] with your chosen url:
Linux and Mac:
python3 SmartClient.py [URL]
Windows:
py SmartClient.py [URL]
