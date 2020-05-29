
from sys import platform

def main():
    #assume that the client runs on win, and the server runs on linux (true for bbai)
    runClient = platform.startswith("win")
    runServer = not runClient

    if runClient:
        from client.client import App
        App().run()

    elif runServer:
        pass #do later

if __name__ == "__main__":main()