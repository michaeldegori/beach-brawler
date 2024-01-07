import json
import socket
import threading
import time

import math

from game_logic.player import Player

active_players = {}
players_in_queue = []
client_sockets = {}


def client_handler(client_socket, client_address):
    print(f"New connection: {client_address}")
    _, port = client_address

    # Determine the player's number based on the current number of active players
    player_number = len(active_players) + 1

    # Create a new player with the initial position
    new_player = Player(port, initial_position(player_number))

    message = {
        "action": "initialize",
        "player_number": player_number,
        "position": new_player.position
    }
    client_socket.send((json.dumps(message) + '\n').encode('ascii'))

    # Add the new player to the active players or queue based on the player count
    if player_number <= 2:
        active_players[client_address] = new_player
        if len(active_players) == 2:
            start_game()
    else:
        players_in_queue.append({client_address: new_player})

    buffer = ""
    while True:
        try:
            data = client_socket.recv(1024).decode('ascii')
            if data:
                buffer += data
                while '\n' in buffer:
                    message, buffer = buffer.split('\n', 1)
                    handle_client_message(message, client_socket, client_address)
            else:
                print(f"Connection closed by {client_address}")
                break
        except Exception as e:
            print(f"Error with {client_address}: {e}")
            break

    client_socket.close()


def handle_client_message(message, client_socket, client_address):
    data = json.loads(message)

    # Determine action sent
    if data['action'] == 'start_moving':
        response = handle_start_moving(data, client_address)
    elif data['action'] == 'stop_moving':
        response = handle_stop_moving(data, client_address)

    elif data['action'] == 'jump':
        response = handle_jump(client_address)
    elif data['action'] == 'attack':
        response = handle_attack(data)
    elif data['action'] == 'restart':
        response = handle_restart(client_address)
    else:
        response = {"status": 'error', "message": "Unknown action"}

    client_socket.send((json.dumps(response) + '\n').encode('ascii'))


def initial_position(player_number):
    if player_number == 1:
        return 100, 318
    elif player_number == 2:
        return 500, 318


def game_loop():
    while True:
        for client_address, player in list(active_players.items()):
            player.update()

            if significant_position_change(player):
                try:
                    update_message = {
                        "action": "update_position",
                        "new_position": player.position,
                    }
                    client_sockets[client_address].send((json.dumps(update_message) + '\n').encode('ascii'))
                    player.last_known_position = player.position
                except Exception as e:
                    print(f"Error sending update to {client_address}: {e}")
                    disconnect_client(client_address)

        # Sleep for 1/30th of a second (30FPS)
        time.sleep(0.033)


def significant_position_change(player):
    # Implement your logic to determine if the position has changed significantly
    # For example:
    position_delta_x = abs(player.position[0] - player.last_known_position[0])
    position_delta_y = abs(player.position[1] - player.last_known_position[1])
    combined_delta = math.sqrt(position_delta_x ** 2 + position_delta_y ** 2)

    return combined_delta > 1


def disconnect_client(client_address):
    active_players.pop(client_address, None)
    client_sockets.pop(client_address, None)


def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    host = socket.gethostname()
    port = 9999

    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Server listening on {host}:{port}")

    threading.Thread(target=game_loop, daemon=True).start()

    while True:
        client_socket, client_address = server_socket.accept()
        client_sockets[client_address] = client_socket

        threading.Thread(target=client_handler, args=(client_socket, client_address)).start()


def start_game():
    print("Game started")
    initial_positions = {player.id: player.position for player in active_players.values()}
    for address, player in list(active_players.items()):
        message = {
            "action": "initialize",
            "player_number": player.id,
            "positions": initial_positions
        }
        try:
            client_sockets[address].send((json.dumps(message) + '\n').encode('ascii'))
        except Exception as e:
            print(f"Error sending initial data to {address}: {e}")
            disconnect_client(address)


def handle_jump(client_address):
    player = active_players.get(client_address)
    if not player:
        return {"status": "error", "message": "Player not found"}

    player.jump()
    print(f"Player {player.id} jumped")

    return {"status": "success", "message": "Jumped"}


def handle_start_moving(data, client_address):
    player = active_players.get(client_address)
    if not player:
        return {"status": "error", "message": "Player not found"}

    player.start_moving(data['direction'])
    return {"status": "success", "action": "start_moving", "message": f"Started moving {data['direction']}"}


def handle_stop_moving(data, client_address):
    player = active_players.get(client_address)
    if not player:
        return {"status": "error", "message": "Player not found"}

    player.stop_moving()
    return {"status": "success", "action": "stop_moving", "message": f"Stopped moving {data['direction']}"}


def handle_attack(data, player_id):
    # Identify the attacker based on player_id
    attacker = None
    for pl in active_players.values():
        if pl.id == player_id:
            attacker = pl
            break

    if not attacker:
        return {"status": "error", "message": "Attacker not found"}

    # Identify the target
    target = None
    for addr, pl in active_players.items():
        if pl.id != player_id:
            target = pl
            break

    if not target:
        return {"status": "error", "message": "Target not found"}

    attacker.attack(target)
    print(f"Attacked! {data}")

    # Check if target is defeated
    if target.health <= 0:
        handle_victory(attacker.id)

    return {"status": "success", "message": f"Attacked player {target.id}", "target_health": target.health}


def handle_victory(winner_address):
    print(f"Player {winner_address} wins!")

    if players_in_queue:
        for address in list(active_players):
            if address != winner_address:
                players_in_queue.append(
                    (active_players[address], Player(address)))  # Add defeated player to end of queue
                break

        next_player_address, next_player = players_in_queue.pop(0)
        active_players[next_player_address] = next_player

        # TODO: Implement start game logic
    else:
        print("No players waiting. Players can restart the match by pressing the space bar.")


def handle_restart(player_address):
    if player_address in active_players:
        # Reset both players
        for address, player in active_players.items():
            player.reset()

        return {"status": "success", "message": "Game restarting"}
    else:
        return {"status": "error", "message": "You're not an active player"}


if __name__ == "__main__":
    start_server()
