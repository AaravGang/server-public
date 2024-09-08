import json
import time
import pickle
import pygame

# Import network and utility modules
from network import Network
from _thread import start_new_thread
from utilities import *

run = True  # Flag to control the running state of the program


# Connect to the server
def connect():
    ip = input("Enter IP: ")  # Prompt for server IP address
    port = input("Enter port: ")  # Prompt for server port
    n = Network(ip, int(port))  # Initialize a Network object
    data = n.connect()  # Connect to the server
    if data:
        curr_user_id = data  # Store the current user ID
        return n, curr_user_id
    else:
        return connect(
            error="Could not connect. Please check if the IP and Port are correct."
        )


# Receive the list of active users from the server
def recieve_active_users():
    try:
        active_users = n.recv()  # Request active users from the server

        if not active_users:
            raise Exception("SERVER CRASHED UNEXPECTEDLY")

        return active_users

    except Exception as e:
        global run
        print("COULD NOT GET ACTIVE USERS FROM SERVER.", e)
        print("DATA RECEIVED WAS: ", active_users)
        run = False  # Stop the main loop if an error occurs


# Send data to the server
def send(data, pickle_data=True):
    sent = n.send(data, pickle_data)  # Send data using Network object
    return sent


# Accept a challenge from another user
def accept_challenge(**kwargs):
    req = {}
    req["accepted"] = {
        "player1_id": kwargs.get("challenger_id"),
        "player2_id": curr_user_id,
        "game": kwargs.get("game"),
    }
    send(req)  # Send the acceptance to the server


# Move/place a piece in the game
def move(game_id, move_id):
    move_req = {}
    move_req["move"] = {"game_id": game_id, "move": move_id}
    send(move_req)  # Send the move to the server


# Send an update details request
def send_update_details_request(changed):
    req = {}
    req["updated"] = changed
    send(req)  # Send the update request to the server


# Send an image to the server in batches
def send_image(img):
    image_bytes = img.tobytes()  # Convert image to bytes
    size = len(image_bytes)  # Get the size of the image data

    # Send the server the size and metadata of the image
    send({"image": {"size": size, "shape": img.shape, "dtype": img.dtype}})

    allowed = n.recv()  # Receive response from the server
    if not allowed.get(
        "image_allowed"
    ):  # Check if the server allowed the image
        raise Exception(allowed.get("error"))
    else:
        print("Started sending image")

        send(image_bytes, pickle_data=False)  # Send the image data

        print("Done sending image")


# Add a user to the active users list
def add_user(user_data):
    user_id = user_data["id"]
    active_users[user_id] = user_data


# Delete a user from the active users list
def del_user(id):
    active_users.pop(id)


# Update user stats
def update_user(id, changed):
    for key in changed:
        if id == curr_user_id:
            curr_user[key] = changed[key]  # Update current user details

        active_users[id][key] = changed[key]  # Update other user's details


# Receive data from the server and handle various updates
def recieve():
    global games, run
    while run:
        data = n.recv()  # Receive data from the server

        # No data received - server is likely down
        if not data:
            print("SERVER DOWN. OR CONNECTION LOST.")
            run = False
            break

        # A new user has connected
        if data.get("connected"):
            add_user(data["connected"])  # Add the new user

        # Someone has disconnected
        if data.get("disconnected"):
            del_user(data["disconnected"])  # Remove the disconnected user

        # Challenge received
        if data.get("challenge"):
            accept_challenge(**data["challenge"])  # Accept the challenge

        # New game started
        if data.get("new_game"):
            game_details = data["new_game"]["details"]  # Game details
            game_id = game_details["game_id"]
            game_name = data["new_game"]["game"]  # Game name

            print(
                f"[BOT]: NEW GAME ({game_name}) | {data['new_game']['identification_dict']}"
            )

            # Setup the game board based on the game name
            if game_name == "tic_tac_toe":
                game_board = TTT_Board(
                    game_id,
                    curr_user_id,
                    X_id=game_details["board"].X_id,
                    O_id=game_details["board"].O_id,
                    move=move,
                    turn_id=game_details["board"].turn_id,
                    rows=game_details["board"].rows,
                    cols=game_details["board"].cols,
                )
            elif game_name == "connect4":
                game_board = Connect4_Board(
                    game_id,
                    curr_user_id,
                    game_details["board"].red_id,
                    game_details["board"].blue_id,
                    move=move,
                    turn_id=game_details["board"].turn_id,
                    rows=game_details["board"].rows,
                    cols=game_details["board"].cols,
                )

            games[game_id] = game_board  # Store the game board

        # Error message received
        if data.get("error"):
            print(f"[BOT]: ERROR : {data['error']}")

        # Game over message
        if data.get("game_over"):
            print(data.get("game_over"))
            game_board.game_over_protocol(
                data["game_over"].get(
                    "indices"), data["game_over"]["winner_id"]
            )

        # Update on a move made by a player
        elif data.get("moved"):
            games[data["moved"]["game_id"]].place(
                data["moved"])  # Update the game board

        # Update user details
        if data.get("updated"):
            update_user(data["updated"]["user_id"], data["updated"]["changed"])


# Setup all variables and connect to the server
def setup(error=None):
    global n, curr_user_id, active_users, curr_user, games

    init_data = connect()  # Connect to the server
    if init_data:
        n, curr_user_id = init_data
    else:
        raise Exception(
            "COULD NOT CONNECT TO SERVER. PLEASE MAKE SURE YOU ARE CONNECTING TO THE RIGHT IP ADDRESS AND PORT, AND THAT YOUR INTERNET IS WORKING."
        )

    active_users = recieve_active_users()  # Load all the active users
    print(active_users)

    curr_user = active_users[curr_user_id]  # Load the current user details

    games = {}  # Initialize games dictionary


# Main function to run the program
def main():
    # Upload image
    with open("bot_img.png", "rb") as f:  # Open image file in binary mode
        img = pygame.image.load(f)
        img = pygame.surfarray.array3d(
            pygame.transform.scale(img, (256, 256),))

        send_image(img)  # Send the image to the server

    # Start receiving data from the server in a separate thread
    start_new_thread(recieve, ())

    # Keep the program running
    while run:
        pass


if __name__ == "__main__":
    setup()  # Setup and connect
    main()  # Run the main function
    print("DISCONNECTED")
