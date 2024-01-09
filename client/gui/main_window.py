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

        self.player_role = initial_data.get('player_role')
        self.player_visuals = [None, None]

        self.key_is_pressed = False
        self.current_moving_direction = None
        self.movement_keys_stack = []
        self.parent.bind('<KeyPress>', self.on_key_press)
        self.parent.bind('<KeyRelease>', self.on_key_release)

        self.handle_initial_data(self.initial_data)

    def handle_initial_data(self, initial_data):
        print("Processing initial data:", initial_data)

        if 'players' in initial_data:
            for idx, player_info in enumerate(initial_data['players']):
                if player_info:
                    self.draw_player(idx, player_info['position'])

    def draw_player(self, player_idx, position):
        width = 100
        height = 150
        x, y = position
        x1, y1 = x - width / 2, y - height / 2
        x2, y2 = x + width / 2, y + height / 2

        color = "blue" if player_idx == 0 else "red"
        self.player_visuals[player_idx] = self.canvas.create_rectangle(x1, y1, x2, y2, fill=color)
        print(f"Drawing player {player_idx + 1} at {position}")

    def update_player_position(self, players_data):
        for idx, player_info in enumerate(players_data):
            if player_info:
                self.move_player_visual(idx, player_info['position'])

    def move_player_visual(self, player_idx, new_position):
        if self.player_visuals[player_idx] is not None:
            width = 100
            height = 150
            x, y = new_position
            x1, y1 = x - width / 2, y - height / 2
            x2, y2 = x + width / 2, y + height / 2
            self.canvas.coords(self.player_visuals[player_idx], x1, y1, x2, y2)
            print(f"Moving player {player_idx + 1} to {new_position}")

    def setup_restart(self):
        self.parent.bind(' ', self.restart_game)

    def restart_game(self, event=None):
        restart_message = {"action": "restart"}
        self.server_connection.send((json.dumps(restart_message) + "\n").encode('ascii'))

    def send_jump(self):
        print("Jumping")

        message = {"action": "jump"}
        self.server_connection.send((json.dumps(message) + "\n").encode('ascii'))

    def on_key_press(self, event):
        self.key_is_pressed = True

        # Add the pressed key to the stack if it's not already in it
        if event.keysym in ['d', 'a'] and event.keysym not in self.movement_keys_stack:
            self.movement_keys_stack.append(event.keysym)

        # Jump
        if event.keysym == 'w':
            self.send_jump()

        # Attack
        if event.keysym == 'i':
            self.send_attack('medium_punch')

        # TODO: Quit / Leave fight
        # if event.keysym == 'q':
        #     self.quit()

        # Send movement command for the most recent key
        self.update_movement()

    def on_key_release(self, event):
        if event.keysym in ['d', 'a']:
            # Remove the released key from the stack
            if event.keysym in self.movement_keys_stack:
                self.movement_keys_stack.remove(event.keysym)

            # Update the movement based on the remaining keys in the stack
            self.update_movement()

    def update_movement(self):
        if self.movement_keys_stack:
            # Get the most recent key
            current_key = self.movement_keys_stack[-1]
            if current_key == 'd':
                self.send_movement('right', True)
            elif current_key == 'a':
                self.send_movement('left', True)
        else:
            # No keys in the stack, stop the movement
            if self.current_moving_direction:
                self.send_movement(self.current_moving_direction, False)
                self.current_moving_direction = None

    def send_movement(self, direction, start):
        # Update the current moving direction
        self.current_moving_direction = direction if start else None
        action = 'start_moving' if start else 'stop_moving'
        message = {"action": action, "direction": direction}
        self.server_connection.send((json.dumps(message) + "\n").encode('ascii'))

    def send_attack(self, attack_type):
        message = {"action": "attack", "type": attack_type}
        self.server_connection.send((json.dumps(message) + "\n").encode('ascii'))

    def handle_server_message(self, message):
        try:
            data = json.loads(message)
            if 'action' in data:
                if data['action'] == 'update_position' and 'players' in data:
                    self.update_player_position(data['players'])
                # handle other actions
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Faulty message: {message}")
        except KeyError as e:
            print(f"Key error: {e} in message: {data}")
        except Exception as e:
            print(f"Unexpected error: {e}")

    def listen_to_server(self):
        #  Continuously listen for messages from the server and handle them

        buffer = ""
        while True:
            try:
                data = self.server_connection.recv(1024).decode('ascii')
                if data:
                    buffer += data
                    while '\n' in buffer:
                        message, buffer = buffer.split('\n', 1)
                        self.handle_server_message(message)
                else:
                    print("Connection closed by server")
                    break
            except Exception as e:
                print(f"Error receiving server message: {e}")
                break

    def run(self):
        listener_thread = threading.Thread(target=self.listen_to_server, daemon=True)
        listener_thread.start()
        self.parent.mainloop()
