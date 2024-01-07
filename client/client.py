import json
import socket
import tkinter as tk

from gui.main_window import GameWindow


class Client:
    def __init__(self):
        self.server_connection = self.create_client_socket()
        self.root = tk.Tk()
        self.game_window = GameWindow(self.root, self.server_connection, self)

        initial_data = self.server_connection.recv(1024).decode('ascii')
        player_info = json.loads(initial_data)
        self.active_player = player_info.get("player_number")

        if self.active_player:
            self.root.title(f"Beach Brawler - Player {self.active_player}")
        else:
            self.root.title("Beach Brawler - Spectating")

        self.root.bind('q', self.quit_application)

    @staticmethod
    def create_client_socket():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        host = socket.gethostname()
        port = 9999

        s.connect((host, port))
        return s

    def quit_application(self, event=None):
        # Close the socket and exit
        self.server_connection.close()
        self.root.quit()

    def run(self):
        self.game_window.run()


if __name__ == "__main__":
    client = Client()
    client.run()
