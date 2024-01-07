import json
import socket
import threading

from game_logic.player import Player

active_players = {}
players_in_queue = []


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
    print("Sending to client:", message)
    client_socket.send(json.dumps(message).encode('ascii'))

    # Add the new player to the active players or queue based on the player count
    if player_number <= 2:
        active_players[client_address] = new_player
        if len(active_players) == 2:
            start_game()
    else:
        players_in_queue.append((client_address, new_player))

    while True:
        try:
            message = client_socket.recv(1024).decode('ascii')
            if message:
                data = json.loads(message)

                # Determine action sent
                if data['action'] == 'move':
                    response = handle_move(data, data['player'])
                elif data['action'] == 'attack':
                    response = handle_attack(data)
                elif data['action'] == 'restart':
                    response = handle_restart(client_address)
                    client_socket.send(json.dumps(response).encode('ascii'))
                else:
                    response = {"status": 'error', "message": "Unknown action"}

                client_socket.send(json.dumps(response).encode('ascii'))
            else:
                print(f"Connection closed by {client_address}")
                break
        except Exception as e:
            print(f"Error with {client_address}: {e}")
            break

    client_socket.close()


def initial_position(player_number):
    if player_number == 1:
        return 100, 240
    elif player_number == 2:
        return 500, 240


def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    host = socket.gethostname()
    port = 9999

    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Server listening on {host}:{port}")

    while True:
        client_socket, client_address = server_socket.accept()

        threading.Thread(target=client_handler, args=(client_socket, client_address)).start()


def start_game():
    print("Game started")
    for address, player in active_players.items():
        initial_positions = {p.id: p.position for p in active_players}
        message = {
            "action": "initialize",
            "positions": initial_positions
        }
        address.send(json.dumps(message).encode('ascii'))


def handle_move(data, player_id):
    player = active_players.get(player_id)
    print(active_players, player, player_id)

    if not player:
        return {"status": "error", "message": "Player not found"}

    player.move(data['direction'])
    print(f"Moved {data['direction']}")

    return {
        "status": "success",
        "message": f"Moved {data['direction']}",
        "new_position": player.position,
        "player": player_id
    }


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
