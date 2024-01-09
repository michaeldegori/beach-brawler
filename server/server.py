import json
import math
import socket
import threading
import time

from game_logic.player import Player

active_players = (None, None)
players_in_queue = []
client_sockets = {}


def client_handler(client_socket, client_address):
    global active_players
    _, port = client_address
    print(f"New connection: {port}")

    # Determine the player's role
    if active_players[0] is None:
        new_player = Player(port, initial_position(1))
        active_players = (new_player, active_players[1])
    elif active_players[1] is None:
        new_player = Player(port, initial_position(2))
        active_players = (active_players[0], new_player)
    else:
        new_player = Player(port)
        players_in_queue.append(new_player)

    player_data = tuple({'id': p.id, 'position': p.position} if p is not None else None for p in active_players)
    message = {
        "action": "initialize",
        "players": player_data
    }
    for _, client_socket in client_sockets.items():
        client_socket.send((json.dumps(message) + '\n').encode('ascii'))

    buffer = ""
    while True:
        try:
            data = client_socket.recv(1024).decode('ascii')
            if data:
                buffer += data
                while '\n' in buffer:
                    message, buffer = buffer.split('\n', 1)
                    handle_client_message(message, client_socket, port)
            else:
                print(f"Connection closed by {port}")
                break
        except Exception as e:
            print(f"Error with {port}: {e}")
            break

    client_socket.close()


def handle_client_message(message, client_socket, port):
    data = json.loads(message)

    # Determine action sent
    if data['action'] == 'start_moving':
        response = handle_start_moving(data, port)
    elif data['action'] == 'stop_moving':
        response = handle_stop_moving(data, port)
    elif data['action'] == 'jump':
        response = handle_jump(port)
    elif data['action'] == 'attack':
        response = handle_attack(data)
    elif data['action'] == 'restart':
        response = handle_restart(port)
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
        # Update each player's state
        for player in active_players:
            if player is not None:
                player.update()

        # After updating, check for position changes and broadcast
        player_data = tuple({'id': p.id, 'position': p.position} if p is not None else None for p in active_players)
        update_message = {
            "action": "update_position",
            "players": player_data
        }

        for player in active_players:
            if player is None:
                continue

            if significant_position_change(player.position, player.last_known_position):
                player.last_known_position = player.position

                # Broadcast the update to all clients
                broadcast_update_to_all_clients(update_message)

        time.sleep(0.033)


def broadcast_update_to_all_clients(update_message):
    for port, client_socket in client_sockets.items():
        try:
            client_socket.send((json.dumps(update_message) + '\n').encode('ascii'))
        except Exception as e:
            print(f"Error sending update to {port}: {e}")
            disconnect_client(port)


def significant_position_change(current_position, last_known_position):
    position_delta_x = abs(current_position[0] - last_known_position[0])
    position_delta_y = abs(current_position[1] - last_known_position[1])
    combined_delta = math.sqrt(position_delta_x ** 2 + position_delta_y ** 2)

    return combined_delta > 1


def disconnect_client(port):
    global active_players, players_in_queue

    # Replace the disconnected player's slot with either None or the next player in the queue
    updated_active_players = []
    for player in active_players:
        if player is not None and player.id == port:
            if players_in_queue:
                # Move the next player from the queue to active players
                updated_active_players.append(players_in_queue.pop(0))
            else:
                updated_active_players.append(None)
        else:
            updated_active_players.append(player)
    active_players = tuple(updated_active_players)

    client_sockets.pop(port, None)


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
        _, port = client_address
        client_sockets[port] = client_socket

        threading.Thread(target=client_handler, args=(client_socket, client_address)).start()


def start_game():
    print("Game started")
    # TODO: do i need all this? Lol
    # initial_positions = {player.id: player.position for player in active_players.values()}
    # for address, player in list(active_players.items()):
    #     message = {
    #         "action": "initialize",
    #         "player_role": player.role,
    #         "positions": initial_positions
    #     }
    #     try:
    #         client_sockets[address].send((json.dumps(message) + '\n').encode('ascii'))
    #     except Exception as e:
    #         print(f"Error sending initial data to {address}: {e}")
    #         disconnect_client(address)


def handle_jump(port):
    player = next((p for p in active_players if p and p.id == port), None)
    if not player:
        return {"status": "error", "message": "Player not found"}

    player.jump()
    print(f"Player {player.id} jumped")

    return {"status": "success", "message": "Jumped"}


def handle_start_moving(data, port):
    player = next((p for p in active_players if p and p.id == port), None)
    if not player:
        return {"status": "error", "message": "Player not found"}

    player.start_moving(data['direction'])
    return {"status": "success", "action": "start_moving", "message": f"Started moving {data['direction']}"}


def handle_stop_moving(data, port):
    player = next((p for p in active_players if p and p.id == port), None)
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
