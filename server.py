import socket
import struct
import math
import pickle
import random
import copy
import json
import time
import pygame
from matplotlib.pyplot import disconnect
from _thread import start_new_thread
from constants import *
from games_logic import TTT_Logic, Connect4_Logic

# IP address and port for the server to bind to
IP = "0.0.0.0"  # Address to bind to (localhost)
PORT = 5555  # Arbitrary non-privileged port
DEFAULT_BYTES = 1024  # Max bytes that can be sent in one message
total_connections_so_far = 0  # Keep track of total connections
total_games_so_far = 0  # Track total games played

# Dictionaries to store active users, connections, send queues, etc.
active_users = {}  # {id:{"conn":conn,"engaged":False}} - Active users data
connections = {}  # Store the connections in a dict, for easy access
send_queue = {}  # Queue for sending data to each user
profile_pictures = {}  # Store profile pics for users

# Pending game requests and ongoing games
pending = {}  # {"challenger_id":(challenged_to,game)} - Pending game requests
games = {}  # {game_id:{players:[],game:<string>,game_details:{board:<Board>}}}

# Dictionary to look up game logic for specific games
games_lookup = {
    "tic_tac_toe": TTT_Logic,
    "connect4": Connect4_Logic,
}  # Easily extendable for more games

# Function to set up a new user


def create_user(conn, addr):
    # Generate a user ID based on the total connections so far
    user_id = str(total_connections_so_far)

    # Create a default username and user stats
    username = f"USER#{user_id}"
    user_stats = {
        "id": user_id,
        "username": username,
        "image": None,
        "color": random.choice(USER_COLORS),  # Randomly assign a color
        "engaged": False,
        "challenged": {},  # Requests this user sent but not yet accepted
        "pending": {},  # Requests this user needs to accept
        "game": None,
        "bot": False,  # User is not a bot by default
    }

    # Add user to the active users and connection dictionaries
    active_users[user_id] = user_stats
    connections[user_id] = conn
    send_queue[user_id] = []  # Initialize an empty send queue

    print(f"[NEW USER] {user_stats['username']} ({user_id})")

    # Send user their ID and all active users' data
    send(user_id, conn)

    # Receive additional user data
    data = recieve_data(conn)
    if not data:  # If no data is received, disconnect the user
        disconnect_user(user_id, user_stats)
        conn.close()
        return None, None

    data = pickle.loads(data)  # Deserialize the received data
    if data.get("updated"):  # If there's updated data, update user stats
        update_user(user_id, data["updated"], send_all=False)

    return user_id, user_stats


# Update user data and optionally broadcast the update to all users
def update_user(user_id, updated, send_all=True):
    updated_copy = updated.copy()

    # Loop through the updated keys to modify user data
    for key in updated:
        if key in active_users[user_id]:
            active_users[user_id][key] = updated[key]  # Update existing data
        else:
            updated_copy.pop(key)  # Remove unknown keys
    if len(updated_copy) == 0:
        return {"error": "Unknown keys!"}  # Return an error for unknown keys
    else:
        if send_all:
            # Broadcast the updated data to all users
            r = {"updated": {"user_id": user_id, "changed": updated}}
            send_to_all(r, user_id, True)

        print(
            f"[UPDATED STATS]: {active_users[user_id]['username']} ({user_id}) \n {updated}"
        )

        return {"message": {"title": "Updated successfully!"}}


# Function to send data in the send queue for a specific user
def execute_send_queue(user_id):

    while active_users.get(user_id):  # Run while user is still active
        try:
            conn = connections[user_id]  # Get the connection for the user
            # Iterate over the send queue and send all items
            for ind, items in enumerate(send_queue[user_id].copy()):
                for item in items:
                    lenData = len(item)
                    if lenData >= DEFAULT_BYTES:  # If data is too large
                        # Use special method for large data
                        send_huge(conn, item)
                    else:
                        send(item, conn, pickle_data=False)

                send_queue[user_id].remove(items)  # Remove items after sending

        # Break the loop if any exception occurs (user might be disconnected)
        except:
            break


# Add items to the user's send queue
def add_to_send_queue(user_id, items):
    send_queue[user_id].append(items)


# Send data to all users (with options to filter certain users)
def send_to_all(
    data, curr_user_id, to_current_user=False, pickle_data=True, to_bots=True
):
    if pickle_data:
        data = pickle.dumps(data)  # Serialize the data
    for user in list(active_users.values()):
        if user["id"] == curr_user_id and not to_current_user:
            continue  # Skip current user if instructed
        if not to_bots and user["bot"]:
            continue  # Skip bots if instructed

        add_to_send_queue(user["id"], [data])


# Send an image to all users
def send_image_to_all(image_data, img):
    for user in list(active_users.values()):
        if not user["bot"]:  # Skip bots
            add_to_send_queue(user["id"], [pickle.dumps(image_data), img])


# Send large data in batches to handle size limitations
def send_huge(conn, data_bytes):
    size = len(data_bytes)
    n_batches = math.ceil(size / DEFAULT_BYTES)  # Calculate number of batches

    # Create batch lengths list
    batch_lengths = [DEFAULT_BYTES] * (n_batches - 1) + [
        size - (n_batches - 1) * DEFAULT_BYTES
    ]
    fmt = "h" * n_batches  # Struct format for batch sizes

    # Inform the receiver about the huge data
    send({"message_type": "huge", "n_batches": n_batches}, conn)

    # Send the batch sizes and the data in parts
    conn.sendall(struct.pack(fmt, *batch_lengths))
    for i in range(n_batches):
        conn.sendall(data_bytes[i * DEFAULT_BYTES: (i + 1) * DEFAULT_BYTES])


# Send data to a connection
def send(data, conn, pickle_data=True):
    try:
        if pickle_data:
            data = pickle.dumps(data)  # Serialize data

        lenData = len(data)
        conn.sendall(
            struct.pack("h", lenData)
        )  # Send the size of the data (2 bytes)
        conn.sendall(data)  # Send the actual data
    except Exception as e:
        print("ERROR TRYING TO SEND DATA: ", e)


# Send active user data to a specific user
def send_all_users(user_id):
    pickledData = pickle.dumps(active_users)
    add_to_send_queue(user_id, [pickledData])
    # Optionally convert the active users data to JSON (commented out)


# Send all profile pictures to a specific user
def send_all_user_images(user_id):

    for key, image_details in profile_pictures.items():
        if image_details is not None:  # If the user has a profile picture
            imageMetaData = {
                "image": {
                    "size": image_details["size"],
                    "user_id": key,
                    "shape": image_details["shape"],
                    "dtype": image_details["dtype"],
                }
            }

            # Serialize metadata and image, then add to send queue
            pickledMetaData = pickle.dumps(imageMetaData)
            encodedImage = image_details["image"]
            add_to_send_queue(user_id, [pickledMetaData, encodedImage])

# Function to recieve data


def recieve_data(conn):
    # Receive the length of the incoming data (2 bytes)
    lenData = conn.recv(2)
    if not lenData:  # If no data is received, the user has disconnected
        return ""

    # Unpack the length of the data from the received bytes (2 bytes)
    lenData = struct.unpack("h", lenData)[0]

    # Receive the data of the specified length
    data = conn.recv(lenData)

    try:
        # Try to unpickle the received data
        pickled = pickle.loads(data)
        if isinstance(pickled, dict) and pickled.get("message_type") == "huge":
            # Handle large data sent in batches
            n_batches = pickled["n_batches"]
            binData = b""
            # Receive batch sizes
            batch_sizes = struct.unpack(
                "h" * n_batches, conn.recv(2 * n_batches))
            for size in batch_sizes:
                try:
                    # Receive each batch of data
                    batchData = conn.recv(size)
                except Exception as e:
                    print(e)

                if not batchData:
                    return ""  # If no data is received, the user has disconnected

                binData += batchData  # Append batch data to complete the data

            return binData  # Return the complete binary data
    except Exception as e:
        # If an exception occurs during unpickling, return the original data
        pass

    return data  # Return the data if it's not a huge message

# Function to properly disconnect user


def disconnect_user(user_id, user_stats):
    try:
        # If the user was engaged in a game, handle game termination
        if active_users[user_id]["engaged"]:
            for game_id in games:
                player_ids = games[game_id]["players"]
                if user_id in player_ids:
                    r = {}
                    r["message"] = {
                        "title": "Player left",
                        "text": "Game over."
                    }
                    r["game_over"] = {
                        "game_id": game_id,
                    }

                    # NOTE: THIS IS ONLY FOR 2 PLAYER GAMES (HARDCODED)
                    for player in games[game_id]["players"].values():
                        id = player["id"]
                        if id != user_id:
                            # Inform the other player that the game is over and they win
                            active_users[id]["engaged"] = False
                            r["game_over"]["winner_id"] = id
                            add_to_send_queue(id, [pickle.dumps(r)])

            # Remove the game from the active games list
            games.pop(game_id)

        # Handle challenges if the user was involved in any
        for challenged_id in active_users[user_id]["challenged"]:
            u = active_users.get(challenged_id)
            if u:
                u["pending"].pop(user_id)
                r = {}
                r["message"] = {
                    "id": f"{user_id}-{challenged_id}-{active_users[user_id]['challenged'][challenged_id]}",
                    "title": "User disconnected.",
                    "text": active_users[user_id]["username"],
                }
                add_to_send_queue(u["id"], [pickle.dumps(r)])

        # Handle pending requests if the user had any
        for pending_id in active_users[user_id]["pending"]:
            u = active_users.get(pending_id)
            if u:
                u["challenged"].pop(user_id)
                r = {}
                r["message"] = {
                    "id": f"{pending_id}-{user_id}-{active_users[user_id]['pending'][pending_id]}",
                    "title": "User disconnected.",
                    "text": active_users[user_id]["username"],
                }
                add_to_send_queue(u["id"], [pickle.dumps(r)])

        # Remove the user from active users, connections, and profile pictures
        user_name = active_users[user_id]["username"]
        if user_id in profile_pictures:
            profile_pictures.pop(user_id)
        active_users.pop(user_id)
        connections.pop(user_id)
        send_queue.pop(user_id)

        # Notify all active users that this user has disconnected
        d = {}
        d["disconnected"] = user_id
        send_to_all(d, user_id, False)

    except Exception as e:
        # If an exception occurs during disconnection, handle cleanup and notification
        print(f"error trying to disconnect user {user_id}", e)
        if user_id in profile_pictures:
            profile_pictures.pop(user_id)
        if user_id in active_users:
            user_name = active_users[user_id]["username"]
            active_users.pop(user_id)
            connections.pop(user_id)
            send_queue.pop(user_id)

        # Notify all active users that this user has disconnected
        d = {}
        d["disconnected"] = user_id
        send_to_all(d, user_id, False)

    print(f"[DISCONNECTED]: {user_name} ({user_id}) | ADDRESS: {addr}")


# Handle communication with a single client
def threaded_client(conn, addr, user_id, user_stats):

    # Send all active users' information to the connected user
    send_all_users(user_id)  # Done

    # If the user is not a bot, send all user images to the connected user
    if not user_stats["bot"]:
        send_all_user_images(user_id)  # Done

    # Notify all other users about this new user's connection
    d = {"connected": user_stats}
    send_to_all(d, user_id, to_current_user=False)  # Done

    while True:
        try:
            # Receive data from the client
            data = recieve_data(conn)

            # If no data is received, the client has disconnected
            if not data:
                break

            # Deserialize the received data from bytes
            data = pickle.loads(data)

            # Initialize a reply dictionary to respond to the client
            reply = {"status": "connected"}

            # Handle challenge requests
            if data.get("challenge"):
                challenged_user_id, game = data["challenge"]

                # Check for errors in the challenge request
                if challenged_user_id not in connections.keys():
                    reply["error"] = "Invalid User ID!"
                elif len(active_users[user_id]["challenged"]) > 0:
                    reply["error"] = "You have already challenged someone!"
                elif len(active_users[user_id]["pending"]) > 0:
                    reply["error"] = "You have a pending request!"
                elif active_users[user_id]["engaged"]:
                    reply["error"] = "You are in a game"
                elif (
                    active_users[challenged_user_id]["engaged"]
                    and not active_users[challenged_user_id]["bot"]
                ):
                    reply["error"] = "User is in a game!"
                elif (
                    len(active_users[challenged_user_id]["pending"])
                    and not active_users[challenged_user_id]["bot"]
                ):
                    reply["error"] = "That user has a pending request!"
                else:
                    # Prepare the challenge request message for the challenged user
                    challenge_req = {}
                    game_id = f"{user_id}-{challenged_user_id}-{game}"
                    challenge_req["message"] = {
                        "title": f"Challenge from {active_users[user_id]['username']}: {game}",
                        "buttons": ["accept", "reject"],
                        "context": {"challenger_id": user_id, "game": game},
                        "closeable": False,
                        "id": game_id,
                    }
                    challenge_req["challenge"] = {
                        "challenger_id": user_id,
                        "game": game,
                    }

                    # Add the challenge request to the challenged user's send queue
                    add_to_send_queue(challenged_user_id, [
                                      pickle.dumps(challenge_req)])

                    # Update the challenge and pending request status for both users
                    active_users[user_id]["challenged"][challenged_user_id] = game
                    active_users[challenged_user_id]["pending"][user_id] = game

                    # Send confirmation to the user who initiated the challenge
                    reply["message"] = {
                        "closeable": False,
                        "title": "Sent successfully",
                        "buttons": ["cancel"],
                        "context": {"opp_id": challenged_user_id, "game": game},
                        "id": game_id,
                    }

                    print(
                        f"[CHALLENGE]: {active_users[user_id]['username']} ({user_id}) challenged {active_users[challenged_user_id]['username']} ({challenged_user_id}) for {game}")

            # Handle canceling a challenge
            if data.get("cancel_challenge"):
                opp_id = data["cancel_challenge"]["opp_id"]
                game = data["cancel_challenge"]["game"]

                if active_users[user_id]["challenged"].get(opp_id):
                    # Remove challenge from the user's challenges and opponent's pending requests
                    active_users[user_id]["challenged"].pop(opp_id)
                    active_users[opp_id]["pending"].pop(user_id)

                    # Send a cancellation message to the opponent
                    reply_to_opp = {}
                    reply_to_opp["cancel"] = {"id": user_id, "game": game}
                    reply_to_opp["message"] = {
                        "id": f"{user_id}-{opp_id}-{game}",
                        "title": "Challenge canceled",
                        "text": f"by {active_users[user_id]['username']}",
                    }

                    add_to_send_queue(opp_id, [pickle.dumps(reply_to_opp)])

                    # Send confirmation to the user who canceled the challenge
                    reply["message"] = {
                        "id": f"{user_id}-{opp_id}-{game}",
                        "title": "Message",
                        "text": "Cancelled successfully.",
                    }

                    print(
                        f"[CANCELLED CHALLENGE] {active_users[user_id]['username']} ({user_id}) to {active_users[opp_id]['username']} ({opp_id})")

                else:
                    reply["error"] = "No pending challenges from that user!"

            # Handle accepting a challenge and starting the game
            if data.get("accepted"):
                d = data["accepted"]

                player1 = active_users.get(d["player1_id"])
                player2 = active_users[user_id]
                game = d["game"]

                # Check for errors in accepting the challenge
                if not player1:
                    reply["error"] = "Invalid user id!"
                elif player1["engaged"]:
                    reply["error"] = "User is in a game!"
                elif player1["challenged"].get(user_id) != game:
                    reply["error"] = f"{player1['username']} hasn't challenged you!"
                elif not games_lookup.get(game):
                    reply["error"] = "Invalid game!"
                else:
                    # Setup the game
                    player1["challenged"].pop(user_id)
                    player2["pending"].pop(player1["id"])

                    game_id = f"{player1['id']}-{user_id}-{game}"
                    board = games_lookup.get(game)(player1, player2)
                    identification_dict = board.get_identification_dict()

                    new_game = {
                        "players": {player1["id"]: player1, player2["id"]: player2},
                        "game": game,
                        "identification_dict": identification_dict,
                        "details": {"game_id": game_id, "board": board},
                    }

                    games[game_id] = new_game

                    player1["engaged"], player2["engaged"] = True, True

                    # Notify both players that the game has started
                    reply_to_player1 = {}
                    reply_to_player1["new_game"] = new_game
                    reply_to_player1["message"] = {
                        "id": game_id,
                        "title": "Game started.",
                        "text": "Have fun!",
                    }

                    add_to_send_queue(
                        player1["id"], [pickle.dumps(reply_to_player1)])

                    reply["new_game"] = new_game
                    reply["message"] = {
                        "title": "Game started.",
                        "text": "Have fun!",
                        "id": game_id,
                    }

                    print(
                        f"[ACCEPTED CHALLENGE]: {player2['username']} ({player2['id']}) from {player1['username']} ({player1['id']})")

            # Handle rejecting a challenge
            if data.get("rejected"):
                d = data["rejected"]
                player1 = active_users.get(d["player1_id"])
                player2 = active_users[user_id]
                game = d["game"]

                # Check for errors in rejecting the challenge
                if not player1:
                    reply["error"] = "Invalid user id!"
                elif not player1["challenged"].get(user_id):
                    reply["error"] = "User hasn't challenged you!"
                else:
                    # Notify the challenger that their challenge was rejected
                    player1["challenged"].pop(user_id)
                    player2["pending"].pop(player1["id"])

                    reply_to_player1 = {}
                    reply_to_player1["message"] = {
                        "id": f"{player1['id']}-{user_id}-{game}",
                        "title": "Challenge rejected",
                        "text": f"for {game} by {player2['username']}",
                    }

                    add_to_send_queue(
                        player1["id"], [pickle.dumps(reply_to_player1)])

                    print(
                        f"[REJECTED CHALLENGE]: {player2['username']} ({player2['id']}) from {player1['username']} ({player1['id']})")

            # Handle quitting a game
            if data.get("quit"):
                game_id = data["quit"]

                if games.get(game_id) and user_id in games.get(game_id)["players"]:
                    r = {}
                    r["message"] = {
                        "title": f"Game ended by {active_users[user_id]['username']}"
                    }

                    winner_id = None

                    # Determine the winner if it's a two-player game
                    if len(games.get(game_id)["players"]) == 2:
                        for id in games.get(game_id)["players"].keys():
                            if id != user_id:
                                winner_id = id
                                break
                        r["game_over"] = {
                            "game_id": game_id,
                            "winner_id": winner_id,
                        }

                    # Disengage all players and delete the game
                    for player in games.get(game_id)["players"].values():
                        player["engaged"] = False
                        add_to_send_queue(player["id"], [pickle.dumps(r)])

                    games.pop(game_id)  # Delete the game

                    print(
                        f"[QUIT GAME]: {active_users[user_id]['username']} ({user_id}) | GAME ID: {game_id}")

                else:
                    reply["error"] = "Invalid game details!"

            # Handle making a move in a game
            if data.get("move") is not None:  # Move may be 0
                game_id = data["move"].get("game_id")
                game = games.get(game_id)
                if not game:
                    reply["error"] = "Game does not exist!"
                else:
                    # Validate and make the move if it's valid
                    is_valid, err = game["details"]["board"].validate(
                        user_id, data["move"].get("move")
                    )
                    if is_valid:
                        game_over, r = game["details"]["board"].move(
                            data["move"].get("move")
                        )
                        r["moved"]["game_id"] = game_id

                        # Handle game over condition
                        if game_over:
                            r["game_over"] = {
                                "game_id": game_id,
                                "winner_id": game_over["winner_id"],
                                "indices": game_over.get("indices"),
                            }

                        for id in game["players"].keys():
                            if game_over:
                                active_users[id]["engaged"] = False

                            add_to_send_queue(id, [pickle.dumps(r)])

                    else:
                        reply["error"] = err

            # Handle updating the user's profile image
            if data.get("image"):
                print(
                    f"[UPLOADING IMAGE]: {active_users[user_id]['username']} ({user_id})")
                size, shape, dtype = (
                    data["image"]["size"],
                    data["image"]["shape"],
                    data["image"]["dtype"],
                )
                if size > max_image_size:
                    error = {"error": "Image too large.",
                             "image_allowed": False}
                    add_to_send_queue(user_id, [pickle.dumps(error)])
                    print(
                        f"[CANCELLED UPLOADING]: {active_users[user_id]['username']} ({user_id})")
                else:
                    add_to_send_queue(
                        user_id, [pickle.dumps({"image_allowed": True})])

                    # Receive the actual image data
                    full_image = recieve_data(conn)

                    # If the user disconnected before the image was fully received
                    if full_image == "":
                        continue

                    print(
                        f"[UPLOADED IMAGE]: {active_users[user_id]['username']} ({user_id})")

                    # Update the profile picture dictionary
                    profile_pictures[user_id] = {
                        "size": size,
                        "user_id": user_id,
                        "shape": shape,
                        "dtype": dtype,
                        "image": full_image,
                    }

                    # Send the updated image to all users
                    image_data = {
                        "image": {
                            "size": size,
                            "user_id": user_id,
                            "shape": shape,
                            "dtype": dtype,
                        }
                    }

                    send_image_to_all(image_data, full_image)

                    reply["message"] = {"title": "Uploaded successfully!"}

                    print(
                        f"[FINISHED UPLOAD]: {active_users[user_id]['username']} ({user_id})")

            # Handle updating user information (e.g., username)
            if data.get("updated"):
                reply.update(update_user(user_id, data["updated"]))

            # Send the reply back to the client
            add_to_send_queue(user_id, [pickle.dumps(reply)])

        except Exception as e:
            # Print an error message if there was an issue processing the data
            print(f"error while processing data from {user_id}", e)
            try:
                print("data received was:", data, "length is:", len(data))
            except:
                print("no data received from", user_id)
            break

    # Clean up when the user disconnects
    disconnect_user(user_id, user_stats)
    # Close the connection
    conn.close()


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    # bind the socket to the host address and port
    s.bind((IP, PORT))
    print("Server started at: ", s.getsockname())

    # listen for connections
    s.listen()
    print("Server has started. waiting for connections...")

    while True:
        # Accept a connection
        conn, addr = s.accept()
        print("[CONNECTED]: ", addr)
        total_connections_so_far += 1  # Increment the totoal connections
        # Generate default stats for new user
        user_id, user_stats = create_user(conn, addr)
        if not user_id:
            continue
        # Start a thread for the new client
        start_new_thread(threaded_client, (conn, addr, user_id, user_stats))
        # Start a thread to send messages to the new client
        start_new_thread(execute_send_queue, (user_id,))
