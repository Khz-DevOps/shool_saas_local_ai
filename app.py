import config
from ui import demo

if __name__ == "__main__":
    print(f"🚀 Starting Agent Chatbot on http://localhost:{config.SERVER_PORT}")
    demo.launch(
        server_port = config.SERVER_PORT,
        inbrowser   = config.OPEN_BROWSER,
        share       = config.SHARE,
        theme       = "soft",
        css         = "footer { display: none !important; }",
    )
