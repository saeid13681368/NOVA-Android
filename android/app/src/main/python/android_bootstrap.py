import os

def start(data_dir):
    os.environ["NOVA_DATA_DIR"] = data_dir
    from core.web_app import start_server
    start_server()

def stop():
    from core.web_app import stop_server
    stop_server()
