import json
import threading
import tkinter as tk


class GameWindow:
    def __init__(self, parent, server_connection, client, initial_data):
        self.parent = parent
        self.server_connection = server_connection
        self.client = client
        self.initial_data = initial_data

        self.canvas = tk.Canvas(self.parent, width=600, height=400)
        self.canvas.pack()
        self.bg_image = tk.PhotoImage(file='client/gui/assets/backgrounds/beach-bg.gif')
        self.canvas.create_image(0, 0, anchor='nw', image=self.bg_image)

        self.player_visual = None

        self.key_is_pressed = False
        self.parent.bind('<KeyPress>', self.on_key_press)
        self.parent.bind('<KeyRelease>', self.on_key_release)

        self.handle_initial_data(self.initial_data)

    def handle_initial_data(self, initial_data):
        print("Processing initial data:", initial_data)
        if 'action' in initial_data and initial_data['action'] == 'initialize':
            if 'player_number' in initial_data:
                self.draw_player(initial_data['position'])
            else:
                for player_id, position in initial_data['positions'].items():
                    self.draw_player(position)

    def draw_player(self, position):
        width = 100
        height = 150
        x, y = position

        # Calculate the top-left and bottom-right coordinates
        x1, y1 = x - width / 2, y - height / 2
        x2, y2 = x + width / 2, y + height / 2

        # Store the visual representation with the player's ID
        self.player_visual = self.canvas.create_rectangle(x1, y1, x2, y2, fill="blue")
        print(f"Drawing player at {position}")

    def update_player_position(self, new_position):
        width = 100
        height = 150
        x, y = new_position

        x1, y1 = x - width / 2, y - height / 2
        x2, y2 = x + width / 2, y + height / 2

        self.canvas.coords(self.player_visual, x1, y1, x2, y2)
        print(f"Moving player to {new_position}")

    def setup_restart(self):
        self.parent.bind(' ', self.restart_game)

    def restart_game(self, event=None):
        restart_message = {"action": "restart"}
        self.server_connection.send(json.dumps(restart_message).encode('ascii'))

    def send_jump(self):
        print("Jumping")

        message = {"action": "jump"}
        self.server_connection.send(json.dumps(message).encode('ascii'))

    def on_key_press(self, event):
        self.key_is_pressed = True

        #  Move right
        if event.keysym == 'd':
            self.send_movement('right', True)
        #  Move left
        if event.keysym == 'a':
            self.send_movement('left', True)
        #  Jump
        if event.keysym == 'w':
            self.send_jump()
        #  Medium punch
        if event.keysym == 'i':
            self.send_attack('medium_punch')

    def on_key_release(self, event):
        self.key_is_pressed = False

        if event.keysym in ['d', 'a']:
            self.send_movement(event.keysym, False)

    def send_movement(self, direction, start):
        action = 'start_moving' if start else 'stop_moving'
        message = {"action": action, "direction": direction}
        self.server_connection.send(json.dumps(message).encode('ascii'))

    def send_attack(self, attack_type):
        message = {"action": "attack", "type": attack_type}
        self.server_connection.send(json.dumps(message).encode('ascii'))

    def handle_server_message(self, message):
        try:
            data = json.loads(message)
            # Check if 'action' is in the message before trying to access it
            if 'action' not in data:
                return

            elif data['action'] == 'update_position':
                self.update_player_position(data['new_position'])
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Faulty message: {message}")
        except KeyError as e:
            print(f"Key error: {e} in message: {data}")
        except Exception as e:
            print(f"Unexpected error: {e}")

    def listen_to_server(self):
        #  Continuously listen for messages from the server and handle them
        while True:
            try:
                server_message = self.server_connection.recv(1024).decode('ascii')
                if server_message:
                    # print("Received from server:", server_message)
                    self.handle_server_message(server_message)
            except Exception as e:
                print(f"Error receiving server message: {e}")
                break

    def run(self):
        listener_thread = threading.Thread(target=self.listen_to_server, daemon=True)
        listener_thread.start()
        self.parent.mainloop()
