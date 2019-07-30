# Voice Stream

Simple voice streaming app

## Running

The following depedencies are required for running this app
- python**3.7**
- pyaudio

```bash
python app.py
```

## Usage

The app will start an interactive console that accepts the following commands

```
exit                - Exit app
serve               - Start server
connect             - Connect to server
stop                - Stop connection
mute                - Mute other party
listen              - Unmute other party
info                - Print current status
```

To connect two computer together, simply type `serve` on one computer and `connect` on the other. 
The `connect` command will start a simple wizard that will guide connection.

In case the wizard can't detect the server, use `connect <ip> <port>` to connect manually.
