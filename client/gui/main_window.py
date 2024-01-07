import json
import socket
import tkinter as tk


class GameWindow:
    def __init__(self, parent, server_connection, client):
        self.parent = parent

        self.server_connection = server_connection
        self.client = client

        self.canvas = tk.Canvas(self.parent, width=600, height=400)
        self.canvas.pack()
        self.bg_image = tk.PhotoImage(file='client/gui/assets/backgrounds/beach-bg.gif')
        self.canvas.create_image(0, 0, anchor='nw', image=self.bg_image)

        self.player_visuals = {}

        self.parent.bind('w', lambda e: self.send_movement('up'))
        self.parent.bind('a', lambda e: self.send_movement('left'))
        self.parent.bind('s', lambda e: self.send_movement('down'))
        self.parent.bind('d', lambda e: self.send_movement('right'))
        self.parent.bind('i', lambda e: self.send_attack('medium_punch'))

    def draw_player(self, player_id, position):
        width = 100
        height = 150
        x, y = position

        # Calculate the top-left and bottom-right coordinates
        x1, y1 = x - width / 2, y - height / 2
        x2, y2 = x + width / 2, y + height / 2

        # Create a rectangle on the canvas to represent the player
        rect = self.canvas.create_rectangle(x1, y1, x2, y2, fill="blue" if player_id == 1 else "red")

        # Store the visual representation with the player's ID
        self.player_visuals[player_id] = rect

    def update_player_position(self, player_id, new_position):
        width = 100
        height = 150
        x, y = new_position

        x1, y1 = x - width / 2, y - height / 2
        x2, y2 = x + width / 2, y + height / 2

        rect = self.player_visuals[player_id]
        self.canvas.coords(rect, x1, y1, x2, y2)

    def setup_restart(self):
        self.parent.bind(' ', self.restart_game)

    def restart_game(self, event=None):
        restart_message = {"action": "restart"}
        self.server_connection.send(json.dumps(restart_message).encode('ascii'))

    def send_movement(self, direction):
        print(f"Moving {direction}")
        active_player = self.client.active_player
        print(active_player)
        message = {"action": "move", "direction": direction, "player": active_player}
        self.server_connection.send(json.dumps(message).encode('ascii'))

    def send_attack(self, attack_type):
        active_player = self.client.active_player
        message = {"action": "attack", "type": attack_type, "player": active_player}
        self.server_connection.send(json.dumps(message).encode('ascii'))

    def handle_server_message(self, message):
        data = json.loads(message)
        print(data)
        if data['action'] == 'initialize':
            if 'player_number' in data:
                self.client.active_player = data['player_number']
                self.draw_player(data['player_number'], data['position'])
            else:
                for player_id, position in data['positions'].items():
                    self.draw_player(player_id, position)
        elif data['action'] == 'update_position':
            self.update_player_position(data['player'], data['new_position'])

    def check_for_server_message(self):
        try:
            server_message = self.server_connection.recv(1024, socket.MSG_DONTWAIT).decode('ascii')
            if server_message:
                print("Received from server:", server_message)
                self.handle_server_message(server_message)
        except BlockingIOError:
            pass
        except Exception as e:
            print(f"Error receiving server message: {e}")
        finally:
            self.parent.after(100, self.check_for_server_message)

    def run(self):
        self.check_for_server_message()
        self.parent.mainloop()
