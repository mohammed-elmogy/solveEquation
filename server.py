import http.server
import socketserver
import urllib.parse
import os
import mimetypes
import re
from solve_equation import *
class Request:
    def __init__(self, handler):
        self.method = handler.command
        self.path = handler.path.split("?")[0]
        self.query = urllib.parse.parse_qs(
            urllib.parse.urlparse(handler.path).query
        )
        self.headers = handler.headers
        self.form = {}
        self.cookies = self.parse_cookies()

        if self.method == "POST":
            content_length = int(handler.headers.get("Content-Length", 0))
            if content_length > 0:
                post_data = handler.rfile.read(content_length).decode("utf-8")
                self.form = urllib.parse.parse_qs(post_data)

    def parse_cookies(self):
        cookies = {}
        cookie_header = self.headers.get("Cookie")
        if cookie_header:
            for pair in cookie_header.split(";"):
                if "=" in pair:
                    key, value = pair.strip().split("=", 1)
                    cookies[key] = value
        return cookies


class Response:
    def __init__(self, handler):
        self.handler = handler
        self.headers = {}

    def set_cookie(self, key, value):
        self.headers["Set-Cookie"] = f"{key}={value}; Path=/"

    def send(self, content, status=200, content_type="text/html"):
        # محتوى جاهز للإرسال
        self.handler.send_response(status)
        self.handler.send_header("Content-type", content_type + "; charset=utf-8")
        for key, value in self.headers.items():
            self.handler.send_header(key, value)
        self.handler.end_headers()
        if isinstance(content, str):
            content = content.encode("utf-8")
        self.handler.wfile.write(content)

    def render_template(self, filename, context=None, status=200):
        """
        يدعم:
         - {{ key }} أو {{key}}  -> يستبدل بقيمة من context إذا موجودة
         - {{Static 'file.png'}} أو {{Static "file.png"}} -> يحول إلى /static/file.png
        """
        filepath = os.path.join("templates", filename)
        if not os.path.exists(filepath):
            return self.send("<h1>Template not found</h1>", 404)

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # 1) استبدال Static tokens أولًا
        content = re.sub(
            r"\{\{\s*Static\s+['\"](.+?)['\"]\s*\}\}",
            lambda m: f"/static/{m.group(1)}",
            content,
        )

        # 2) استبدال المتغيرات العامة {{ key }} مع دعم المسافات
        def replace_var(match):
            key = match.group(1).strip()
            if context and key in context:
                return str(context[key])
            # لو مش موجود في context نتركه فارغ بدل إبقاء التوكن
            return ""

        content = re.sub(r"\{\{\s*(.+?)\s*\}\}", replace_var, content)

        # إرسال المحتوى الناتج
        self.send(content, status)

    def send_file(self, filepath, status=200):
        if os.path.exists(filepath):
            mime_type, _ = mimetypes.guess_type(filepath)
            if not mime_type:
                mime_type = "application/octet-stream"
            self.handler.send_response(status)
            self.handler.send_header("Content-type", mime_type)
            self.handler.end_headers()
            with open(filepath, "rb") as f:
                self.handler.wfile.write(f.read())
        else:
            self.send("<h1>File not found</h1>", 404)


class App:
    def __init__(self, port=8000):
        self.routes = {}
        self.port = port

    def route(self, path):
        def decorator(func):
            self.routes[path] = func
            return func
        return decorator

    def start(self):
        app = self

        class CustomHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                req = Request(self)
                res = Response(self)

                # دعم static
                if req.path.startswith("/static/"):
                    filepath = req.path.lstrip("/")
                    return res.send_file(filepath)

                handler = app.routes.get(req.path)
                if handler:
                    try:
                        handler(req, res)   # لا تُعد return القيمة
                    except Exception as e:
                        res.send(f"<h1>Server error</h1><pre>{e}</pre>", 500)
                    # handler(req,res)
                else:
                    res.send("<h1>404 Not Found</h1>", 404)

            def do_POST(self):
                req = Request(self)
                res = Response(self)
                handler = app.routes.get(req.path)
                if handler:
                    # try:
                        # handler(req, res)
                    # except Exception as e:
                        # res.send(f"<h1>Server error</h1><pre>{e}</pre>", 500)
                    handler(req,res)
                else:
                    res.send("<h1>404 Not Found</h1>", 404)

        with socketserver.TCPServer(("", self.port), CustomHandler) as httpd:
            print(f"Server running on http://localhost:{self.port}")
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\nServer stopped.")


# --------------------------
# مثال استخدام
# --------------------------
app = App(8000)
@app.route("/")
def main(req, res):
    if req.method == "GET":
        # أول مرة يفتح الصفحة
        return res.render_template("index.html")

    elif req.method == "POST":
        # جالك بيانات من الفورم
        equation = req.form.get("equation", [""])[0]
        result=run(equation)
        j=''
        for i in result:
            j+="<br>"+i
        return res.render_template("index.html", {"solve":j,"j":equation.replace((';'),('<br>'))})

if __name__ == "__main__":
    app.start()
