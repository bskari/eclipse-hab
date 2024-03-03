from http.server import BaseHTTPRequestHandler, HTTPServer


class GoogleEarthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "* application/vnd.google-earth.kml+xml")
        self.end_headers()
        with open("balloon.kml") as file:
            self.wfile.write(file.read().encode())


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8080), GoogleEarthHandler)
    server.serve_forever()
