'''
Communicate with MPD via the python-mpd2 module

Inputs :
    - path (either 

Outputs : 
    - MPD action
    - write to state files ?
'''
from mpd import MPDClient

class MPDController:
    def __init__(self, host='localhost', port=6600):
        self.client = MPDClient()
        self.client.connect(host, port)

    def play(self):
        self.client.play()

    def pause(self):
        self.client.pause()

    def add_to_playlist(self, file_path):
        self.client.add(file_path)

    def clear_playlist(self):
        self.client.clear()

    def get_current_song(self):
        return self.client.currentsong()
