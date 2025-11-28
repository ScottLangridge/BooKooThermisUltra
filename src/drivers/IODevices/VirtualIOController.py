from flask import Flask, send_file
from PIL import Image
import io
import threading

from .IOController import IOController


class VirtualIOController(IOController):
    """
    Virtual implementation of IOController using a Flask web server.
    Provides a browser-based interface for development and testing.
    """

    def __init__(self, host="0.0.0.0", port=5000):
        super().__init__()

        self.app = Flask(__name__)
        self.host = host
        self.port = port

        # Internal state
        self._current_image = Image.new("RGB", (240, 240), "white")

        # Setup Flask routes
        self._setup_routes()

        # Start Flask server in a separate daemon thread
        self._thread = threading.Thread(target=self.app.run, kwargs={
            "host": self.host, "port": self.port, "debug": False, "use_reloader": False
        })
        self._thread.daemon = True
        self._thread.start()

    def draw(self, img: Image.Image):
        """
        Display an image on the virtual device.

        Args:
            img: PIL Image object, must be 240x240 pixels
        """
        if img.size != (240, 240):
            raise ValueError("Image must be 240x240 pixels")
        self._current_image = img.copy()

    def _setup_routes(self):
        @self.app.route("/frame")
        def frame():
            # Return the current PIL image
            buf = io.BytesIO()
            self._current_image.save(buf, format="PNG")
            buf.seek(0)
            return send_file(buf, mimetype="image/png")

        @self.app.route("/display")
        def display():
            # Serve the web page with buttons and screen
            return """
            <html>
                <body style="
                    margin:0;
                    background:white;
                    height:100vh;
                    display:flex;
                    justify-content:center;
                    align-items:center;
                    font-family:sans-serif;
                " tabindex="0">
                    <!-- Left joystick -->
                    <div style="display:flex; flex-direction:column; align-items:center; margin-right:40px;">
                        <button onclick="send('up'); this.blur();" style="width:60px;height:60px;">▲</button>
                        <div style="height:10px;"></div>
                        <div style="display:flex; flex-direction:row; align-items:center;">
                            <button onclick="send('left'); this.blur();" style="width:60px;height:60px;">◀</button>
                            <button onclick="send('center'); this.blur();" style="width:60px;height:60px; border-radius:50%; margin:0 10px;">●</button>
                            <button onclick="send('right'); this.blur();" style="width:60px;height:60px;">▶</button>
                        </div>
                        <div style="height:10px;"></div>
                        <button onclick="send('down'); this.blur();" style="width:60px;height:60px;">▼</button>
                    </div>

                    <!-- Display -->
                    <img id="screen" src="/frame" style="width:240px;height:240px; image-rendering:pixelated; border:1px solid #ccc;">

                    <!-- Right buttons A/B -->
                    <div style="display:flex; flex-direction:column; align-items:center; margin-left:40px;">
                        <button onclick="send('A'); this.blur();" style="width:60px;height:60px;font-size:24px;">A</button>
                        <div style="height:20px;"></div>
                        <button onclick="send('B'); this.blur();" style="width:60px;height:60px;font-size:24px;">B</button>
                    </div>

                    <script>
                        // Auto-focus the body on load so keyboard events work immediately
                        document.body.focus();

                        setInterval(() => {
                            document.getElementById("screen").src = "/frame?ts=" + Date.now();
                        }, 1000);

                        function send(action) {
                            fetch('/input/' + action).catch(err => console.log(err));
                        }

                        // Keyboard event handling
                        document.addEventListener('keydown', (event) => {
                            const keyMap = {
                                'ArrowUp': 'up',
                                'ArrowDown': 'down',
                                'ArrowLeft': 'left',
                                'ArrowRight': 'right',
                                ' ': 'center',
                                'a': 'A',
                                'b': 'B'
                            };

                            const action = keyMap[event.key];
                            if (action) {
                                event.preventDefault();  // Prevent default browser behavior (e.g., scrolling)
                                event.stopPropagation(); // Prevent event from bubbling
                                send(action);
                            }
                        });
                    </script>
                </body>
            </html>
            """

        @self.app.route("/input/<action>")
        def input_action(action):
            # Call the appropriate callback
            callbacks = {
                "up": self.on_up,
                "down": self.on_down,
                "left": self.on_left,
                "right": self.on_right,
                "center": self.on_center,
                "A": self.on_a,
                "B": self.on_b
            }
            if action in callbacks:
                callbacks[action]()
            return "ok"
