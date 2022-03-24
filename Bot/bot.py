import json, time, pickle, pygame

# import numpy as np
from network import Network
from _thread import start_new_thread
from utilities import *

run = True


# connect to the server
def connect():
    ip = input("Enter IP: ")
    port = input("Enter port: ")
    n = Network(ip, int(port))  # initialise a network
    data = n.connect()  # connect to the server
    if data:
        curr_user_id = data
        return n, curr_user_id
    else:
        return connect(
            error="Could not connect. Please check if the IP and Port are correct."
        )


# recieve the list of active users from the server
def recieve_active_users():

    try:
        active_users = n.recv()

        if not active_users:
            raise Exception("SERVER CRASHED UNEXPECTEDLY")

        return active_users

    except Exception as e:
        global run
        print("COULD NOT GET ACTIVE USRERS FROM SERVER.", e)
        print("DATA RECIEVED WAS: ", active_users)
        run = False


# send something to the server
def send(data, pickle_data=True):
    sent = n.send(data, pickle_data)
    return sent


# accept challenge from another user
def accept_challenge(**kwargs):
    req = {}
    req["accepted"] = {
        "player1_id": kwargs.get("challenger_id"),
        "player2_id": curr_user_id,
        "game": kwargs.get("game"),
    }
    send(req)


# move/place a piece
def move(game_id, move_id):
    move_req = {}
    move_req["move"] = {"game_id": game_id, "move": move_id}
    send(move_req)


# send an update details request
def send_update_details_request(changed):
    req = {}
    req["updated"] = changed
    send(req)


# send an image in batches
def send_image(img):
    image_bytes = img.tobytes()
    size = len(image_bytes)

    # send the server the size of the image
    send({"image": {"size": size, "shape": img.shape, "dtype": img.dtype}})

    allowed = n.recv()
    if not allowed.get(
        "image_allowed"
    ):  # image is prolly too large, and rejected by server
        raise Exception(allowed.get("error"))
    else:

        print("started sending image")

        send(image_bytes, pickle_data=False)

        print("done sending image")


# add an user to the active users
def add_user(user_data):
    user_id = user_data["id"]
    active_users[user_id] = user_data


# delete a user
def del_user(id):
    active_users.pop(id)


# update user stats
def update_user(id, changed):
    for key in changed:
        if id == curr_user_id:
            curr_user[key] = changed[key]

        active_users[id][key] = changed[key]


# recieve some data from the server
def recieve():
    global games, run
    while run:
        data = n.recv()

        # no data recieved - server is likely down.
        if not data:
            print("SERVER DOWN. OR CONNECTION LOST.")
            run = False
            break

        # a new user has connected
        if data.get("connected"):
            # data["connected"] is the details of that user
            # add the user to all required dicts
            add_user(data["connected"])

        # someone has disconnected
        if data.get("disconnected"):
            # data["disconnected"] is the id of that user
            # remove that user from all dicts
            del_user(data["disconnected"])

        if data.get("challenge"):
            accept_challenge(**data["challenge"])

        # new game started
        if data.get("new_game"):

            game_details = data["new_game"]["details"]  # {game_id, board}
            game_id = game_details["game_id"]
            game_name = data["new_game"]["game"]  # game name

            print(
                f"[BOT]: NEW GAME ({game_name}) | {data['new_game']['identification_dict']}"
            )

            # setup the game accordingly
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

            games[game_id] = game_board

        if data.get("error"):
            print(f"[BOT]: ERROR : {data['error']}")

        # game over
        if data.get("game_over"):
            print(data.get("game_over"))
            game_board.game_over_protocol(
                data["game_over"].get("indices"), data["game_over"]["winner_id"]
            )

        # someone has moved,update on this screen
        elif data.get("moved"):
            # move on the board, and also send the request for this players move
            games[data["moved"]["game_id"]].place(data["moved"])

        # update a user's details
        if data.get("updated"):
            update_user(data["updated"]["user_id"], data["updated"]["changed"])


# setup all the variables and connect to the server
def setup(error=None):
    global n, curr_user_id, active_users, curr_user, games

    init_data = connect()
    if init_data:
        n, curr_user_id = init_data
    else:
        raise Exception(
            "COULD NOT CONNECT TO SERVER. PLEASE MAKE SURE YOU ARE CONNECTING TO THE RIGHT IP ADDRESS AND PORT, AND THAT YOU INTERNET IS WORKING."
        )

    active_users = recieve_active_users()  # load all the users
    print(active_users)

    curr_user = active_users[curr_user_id]  # load the current user

    games = {}


# main function, put everything together
def main():
    # upload image
    with open("bot_img.png") as f:
        img = pygame.image.load(f)
        img = pygame.surfarray.array3d(pygame.transform.scale(img, (256, 256),))

        send_image(img)

    # recieve data from the server in a seperate thread
    start_new_thread(recieve, ())

    # keep the program running
    while run:
        pass


if __name__ == "__main__":
    setup()
    main()
    print("DISCONNECTED")
