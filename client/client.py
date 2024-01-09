import json
import socket
import tkinter as tk

from gui.main_window import GameWindow


class Client:
    def __init__(self):
        self.server_connection = self.create_client_socket()

        initial_data = self.server_connection.recv(1024).decode('ascii')
        self.initial_data = json.loads(initial_data)

        self.root = tk.Tk()
        self.game_window = GameWindow(self.root, self.server_connection, self, self.initial_data)

        # Determine player role based on initial data
        self.player_id = None
        self.player_role = self.determine_player_role(self.initial_data.get("players"))

        subtitle = 'Spectating' if self.player_role == 'spectator' else self.player_role
        self.root.title(f"Beach Brawler - {subtitle}")

        self.root.bind('q', self.quit_application)

    def determine_player_role(self, players):
        self.player_id = None
        for idx, player_info in enumerate(players):
            if player_info:
                _, my_port = self.server_connection.getsockname()

                if my_port == player_info['id']:
                    self.player_id = player_info['id']
                    return 'player1' if idx == 0 else 'player2'
        return 'spectator'

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
