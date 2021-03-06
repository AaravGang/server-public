import socket, struct, math, pickle, random, copy, json, time, pygame
from matplotlib.pyplot import disconnect
from _thread import start_new_thread
from constants import *
from games_logic import TTT_Logic, Connect4_Logic

# import numpy as np


IP = "0.0.0.0"  # Address to bind to
PORT = 5555  # Arbitrary non-privileged port
DEFAULT_BYTES = 1024  # max bytes to be sent in one message
total_connections_so_far = 0
total_games_so_far = 0

active_users = {}  # {id:{"conn":conn,"engaged":False}}
connections = {}  # store the connections in a dict, for easy access
send_queue = {}  # queue for sending data to each user
profile_pictures = {}  # store all the profile pics or users

pending = {}  # {"challenger_id":(challenged_to,game)}
games = {}  # {game_id:{players:[],game:<string>,game_details:{board:<Board>}}}

games_lookup = {
    "tic_tac_toe": TTT_Logic,
    "connect4": Connect4_Logic,
}  # maybe add more games in the future

# a function to set up a user
def create_user(conn, addr):
    # generate the users default stats
    user_id = str(total_connections_so_far)

    username = f"USER#{user_id}"
    user_stats = {
        "id": user_id,
        "username": username,
        "image": None,
        "color": random.choice(USER_COLORS),
        "engaged": False,
        "challenged": {},  # requests this user has sent and are yet to be accepted by another
        "pending": {},  # requests this user needs to accept
        "game": None,
        "bot": False,
    }

    # add this user to the active users
    active_users[user_id] = user_stats
    connections[user_id] = conn
    send_queue[user_id] = []

    print(f"[NEW USER] {user_stats['username']} ({user_id})")

    # send this user some start up info
    # (this users id, all active users)
    send(user_id, conn)

    data = recieve_data(conn)
    if not data:
        disconnect_user(user_id, user_stats)
        conn.close()
        return None, None

    data = pickle.loads(data)
    if data.get("updated"):
        update_user(user_id, data["updated"], send_all=False)

    return user_id, user_stats


def update_user(user_id, updated, send_all=True):
    updated_copy = updated.copy()

    for key in updated:
        if key in active_users[user_id]:
            active_users[user_id][key] = updated[key]
        else:
            updated_copy.pop(key)
    if len(updated_copy) == 0:
        return {"error": "Unknown keys!"}
    else:
        if send_all:
            r = {"updated": {"user_id": user_id, "changed": updated}}
            send_to_all(r, user_id, True)

        print(
            f"[UPDATED STATS]: {active_users[user_id]['username']} ({user_id}) \n {updated}"
        )

        return {"message": {"title": "Updated successfully!"}}


def execute_send_queue(user_id):

    while active_users.get(user_id):
        try:
            # send queue is expected to be list of lists
            conn = connections[user_id]
            for ind, items in enumerate(send_queue[user_id].copy()):
                for item in items:
                    # item is supposed to be binary data
                    lenData = len(item)
                    if lenData >= DEFAULT_BYTES:
                        send_huge(conn, item)

                    else:
                        send(item, conn, pickle_data=False)

                send_queue[user_id].remove(items)
                # time.sleep(2)

        except:
            break


def add_to_send_queue(user_id, items):
    send_queue[user_id].append(items)


# send some data to all connected users
def send_to_all(
    data, curr_user_id, to_current_user=False, pickle_data=True, to_bots=True
):
    if pickle_data:
        data = pickle.dumps(data)
    for user in list(active_users.values()):
        if user["id"] == curr_user_id and not to_current_user:
            continue
        if not to_bots and user["bot"]:
            continue

        add_to_send_queue(user["id"], [data])


def send_image_to_all(image_data, img):
    for user in list(active_users.values()):
        if not user["bot"]:
            add_to_send_queue(user["id"], [pickle.dumps(image_data), img])


def send_huge(conn, data_bytes):
    size = len(data_bytes)
    n_batches = math.ceil(size / DEFAULT_BYTES)

    batch_lengths = [DEFAULT_BYTES] * (n_batches - 1) + [
        size - (n_batches - 1) * DEFAULT_BYTES
    ]
    fmt = "h" * n_batches

    # send the data in batches
    send({"message_type": "huge", "n_batches": n_batches}, conn)

    conn.sendall(struct.pack(fmt, *batch_lengths))
    for i in range(n_batches):
        conn.sendall(data_bytes[i * DEFAULT_BYTES : (i + 1) * DEFAULT_BYTES])


def send(data, conn, pickle_data=True):
    try:
        if pickle_data:
            data = pickle.dumps(data)

        lenData = len(data)
        conn.sendall(
            struct.pack("h", lenData)
        )  # send the size of data padded to 2 bytes
        conn.sendall(data)
    except Exception as e:
        print("ERROR TRYING TO SEND DATA: ", e)


def send_all_users(user_id):
    pickledData = pickle.dumps(active_users)
    add_to_send_queue(user_id, [pickledData])
    # active_users_data_bytes = json.dumps(active_users).encode("utf-8")


def send_all_user_images(user_id):

    for key, image_details in profile_pictures.items():

        if image_details is not None:
            imageMetaData = {
                "image": {
                    "size": image_details["size"],
                    "user_id": key,
                    "shape": image_details["shape"],
                    "dtype": image_details["dtype"],
                }
            }

            pickledMetaData = pickle.dumps(imageMetaData)
            encodedImage = image_details["image"]
            add_to_send_queue(user_id, [pickledMetaData, encodedImage])


def recieve_data(conn):
    lenData = conn.recv(2)
    if not lenData:  # user disconnected
        return ""

    lenData = struct.unpack("h", lenData)[
        0
    ]  # length of data will be padded to 2  bytes

    data = conn.recv(lenData)

    try:
        pickled = pickle.loads(data)
        if isinstance(pickled, dict) and pickled.get("message_type") == "huge":
            n_batches = pickled["n_batches"]
            binData = b""
            batch_sizes = struct.unpack("h" * n_batches, conn.recv(2 * n_batches))
            for size in batch_sizes:
                try:
                    batchData = conn.recv(size)
                except Exception as e:
                    print(e)

                if not batchData:
                    return ""  # user disconnected

                binData += batchData

            return binData
    except Exception as e:
        pass

    return data


def disconnect_user(user_id, user_stats):
    try:
        # this player was in a game when he left, deal with it
        if active_users[user_id]["engaged"]:
            for game_id in games:
                player_ids = games[game_id]["players"]
                if user_id in player_ids:

                    r = {}
                    r["message"] = {"title": "Player left", "text": "Game over."}
                    r["game_over"] = {
                        "game_id": game_id,
                    }

                    # NOTE: THIS IS ONLY FOR 2 PLAYER GAMES (HARDCODED)
                    for player in games[game_id]["players"].values():
                        id = player["id"]
                        if id != user_id:
                            # this user has quit the game, so the other id wins
                            active_users[id]["engaged"] = False
                            r["game_over"]["winner_id"] = id

                            add_to_send_queue(id, [pickle.dumps(r)])

            games.pop(game_id)  # delete that game

        # if the user has challenged
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

        # if this user has a pending request
        for pending_id in active_users[user_id]["pending"]:
            u = active_users.get(
                pending_id
            )  # pending id is the id of the one who challenged, i.e player1
            if u:
                u["challenged"].pop(user_id)
                r = {}
                r["message"] = {
                    "id": f"{pending_id}-{user_id}-{active_users[user_id]['pending'][pending_id]}",
                    "title": "User disconnected.",
                    "text": active_users[user_id]["username"],
                }
                add_to_send_queue(u["id"], [pickle.dumps(r)])

        user_name = active_users[user_id]["username"]

        # remove this user from active users and connections and profile pics
        if user_id in profile_pictures:
            profile_pictures.pop(user_id)
        active_users.pop(user_id)
        connections.pop(user_id)
        send_queue.pop(user_id)

        # let all active users know this user has disconnected
        # this user is not included in the active users
        d = {}
        d["disconnected"] = user_id
        send_to_all(d, user_id, False)

    except Exception as e:
        print(f"error trying to disconnect user {user_id}", e)
        # remove this user from active users and connections and profile pics
        if user_id in profile_pictures:
            profile_pictures.pop(user_id)

        user_name = active_users[user_id]["username"]
        active_users.pop(user_id)
        connections.pop(user_id)
        send_queue.pop(user_id)

        # let all active users know this user has disconnected
        # this user is not included in the active users
        d = {}
        d["disconnected"] = user_id
        send_to_all(d, user_id, False)

    print(f"[DISCONNECTED]: {user_name} ({user_id}) | ADDRESS: {addr}")


# deal with sending and recieving data from and to a user
def threaded_client(conn, addr, user_id, user_stats):

    # send all active users' info to this one
    send_all_users(user_id)  # done

    if not user_stats["bot"]:
        print("yes")
        send_all_user_images(user_id)  # done

    # send all other users this user's stats
    d = {"connected": user_stats}
    send_to_all(d, user_id, to_current_user=False)  # done

    while True:
        try:

            data = recieve_data(conn)

            # client disconnected
            if not data:
                break

            data = pickle.loads(data)  # data comes in as pickle encoded bytes
            reply = {"status": "connected"}  # initiate a reply, to send to the user

            if data.get("challenge"):

                # challenge will come in as (challenged_user_id, game_name)

                challenged_user_id, game = data["challenge"]

                # deal with edge cases that could raise errors
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
                    # prepare a challenge request, to send to challenged_user
                    challenge_req = {}
                    # a unique game id
                    game_id = f"{user_id}-{challenged_user_id}-{game}"
                    # the client code knows how to deal with extra props being sent in with the message
                    # send an accept or reject button message to the challenged user
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

                    add_to_send_queue(challenged_user_id, [pickle.dumps(challenge_req)])

                    # set the respective flags of the players involved
                    active_users[user_id]["challenged"][challenged_user_id] = game
                    active_users[challenged_user_id]["pending"][user_id] = game

                    # send a cancel button message to the user who challenged
                    reply["message"] = {
                        "closeable": False,
                        "title": "Sent succesfully",
                        "buttons": ["cancel"],
                        "context": {"opp_id": challenged_user_id, "game": game},
                        "id": game_id,
                    }

                    print(
                        f"[CHALLENGE]: {active_users[user_id]['username']} ({user_id}) challenged {active_users[challenged_user_id]['username']} ({challenged_user_id}) for {game}"
                    )

            # this user is trying to cancel a challenge request
            if data.get("cancel_challenge"):
                opp_id = data["cancel_challenge"]["opp_id"]  # the opponents id
                game = data["cancel_challenge"][
                    "game"
                ]  # the game this user has challenged for

                if active_users[user_id]["challenged"].get(opp_id):
                    # remove the opponent from this users challenges
                    if active_users[user_id]["challenged"].get(opp_id):
                        active_users[user_id]["challenged"].pop(opp_id)
                    # remove this user from the opponent's pending requests
                    if active_users[opp_id]["pending"].get(user_id):
                        active_users[opp_id]["pending"].pop(user_id)

                    # send a cancelled message
                    reply_to_opp = {}
                    reply_to_opp["cancel"] = {"id": user_id, "game": game}
                    reply_to_opp["message"] = {
                        "id": f"{user_id}-{opp_id}-{game}",
                        "title": "Challenged cancelled",
                        "text": f"by {active_users[user_id]['username']}",
                    }

                    add_to_send_queue(opp_id, [pickle.dumps(reply_to_opp)])

                    reply["message"] = {
                        "id": f"{user_id}-{opp_id}-{game}",
                        "title": "Message",
                        "text": "Cancelled successfully.",
                    }

                    print(
                        f"[CANCELLED CHALLENGE] {active_users[user_id]['username']} ({user_id}) to {active_users[opp_id]['username']} ({opp_id})"
                    )

                else:
                    reply["error"] = "No pending challenges from that user!"

            # a challenge has been accepted, start the game
            if data.get("accepted"):
                d = data["accepted"]

                player1 = active_users.get(d["player1_id"])  # the one who challenged
                player2 = active_users[user_id]  # this user
                game = d["game"]

                # handle edge cases
                if not player1:
                    reply["error"] = "Invalid user id!"
                elif player1["engaged"]:
                    reply["error"] = "User is in a game!"
                elif player1["challenged"].get(user_id) != game:
                    reply["error"] = f"{player1['username']} hasn't challenged you!"
                elif not games_lookup.get(game):
                    reply["error"] = "Invalid game!"

                # everything's good, setup the game
                else:
                    player1["challenged"].pop(user_id)
                    player2["pending"].pop(player1["id"])

                    game_id = f"{player1['id']}-{user_id}-{game}"  # a unique game_id
                    board = games_lookup.get(game)(
                        player1, player2
                    )  # generate a game board according to the game

                    # player information (who is what) | ex: {player1_id:"X",player2_id:"O"}
                    identification_dict = board.get_identification_dict()

                    # setup the game
                    new_game = {
                        "players": {player1["id"]: player1, player2["id"]: player2},
                        "game": game,
                        "identification_dict": identification_dict,
                        "details": {"game_id": game_id, "board": board,},
                    }

                    # add this game to the existing dict of games
                    games[game_id] = new_game

                    # both these players are now in a game
                    player1["engaged"], player2["engaged"] = True, True

                    # send a message saying the game has started!
                    reply_to_player1 = {}
                    reply_to_player1["new_game"] = new_game
                    reply_to_player1["message"] = {
                        "id": game_id,
                        "title": "Game started.",
                        "text": "Have fun!",
                    }

                    add_to_send_queue(player1["id"], [pickle.dumps(reply_to_player1)])

                    reply["new_game"] = new_game

                    reply["message"] = {
                        "title": "Game started.",
                        "text": "Have fun!",
                        "id": game_id,
                    }

                    print(
                        f"[ACCEPTED CHALLENGE]: {player2['username']} ({player2['id']}) from {player1['username']} ({player1['id']})"
                    )

            # challenge rejected
            if data.get("rejected"):
                d = data["rejected"]
                player1 = active_users.get(d["player1_id"])  # the one who challenged
                player2 = active_users[user_id]  # this user
                game = d["game"]

                # check for edge cases
                if not player1:
                    reply["error"] = "Invalid user id!"

                elif not player1["challenged"].get(user_id):
                    reply["error"] = "User hasn't challenged you!"

                else:
                    # disengage both players and send respective messages
                    player1["challenged"].pop(user_id)
                    player2["pending"].pop(player1["id"])
                    reply_to_player1 = {}
                    reply_to_player1["message"] = {
                        "id": f"{player1['id']}-{user_id}-{game}",
                        "title": "Challenge rejected",
                        "text": f"for {game} by {player2['username']}",
                    }

                    add_to_send_queue(player1["id"], [pickle.dumps(reply_to_player1)])

                    print(
                        f"[REJECTED CHALLENGE]: {player2['username']} ({player2['id']}) from {player1['username']} ({player1['id']})"
                    )

            # quit a game
            if data.get("quit"):
                game_id = data["quit"]

                if games.get(game_id) and user_id in games.get(game_id)["players"]:

                    r = {}
                    r["message"] = {
                        "title": f"Game ended by {active_users[user_id]['username']}"
                    }

                    # set the respective winners
                    winner_id = None

                    # figuring out the winner
                    if len(games.get(game_id)["players"]) == 2:
                        for id in games.get(game_id)["players"].keys():
                            if id != user_id:
                                winner_id = id
                                break
                        r["game_over"] = {
                            "game_id": game_id,
                            "winner_id": winner_id,
                        }

                    # disengage all players involved in the game
                    # NOTE: THIS WILL ONLY WORK AS EXPECTED IF IT IS A 2 PLAYER GAME
                    for player in games.get(game_id)["players"].values():
                        player["engaged"] = False

                        add_to_send_queue(player["id"], [pickle.dumps(r)])

                    games.pop(game_id)  # delete this game

                    print(
                        f"[QUIT GAME]: {active_users[user_id]['username']} ({user_id}) | GAME ID: {game_id}"
                    )

                else:
                    reply["error"] = "Invalid game details!"

            # the player has made a move
            if data.get("move") is not None:  # move maybe 0
                game_id = data["move"].get("game_id")
                game = games.get(game_id)
                if not game:
                    reply["error"] = "Game does not exist!"

                else:
                    # if this move is valid, then move
                    is_valid, err = game["details"]["board"].validate(
                        user_id, data["move"].get("move")
                    )
                    if is_valid:

                        game_over, r = game["details"]["board"].move(
                            data["move"].get("move")
                        )
                        r["moved"]["game_id"] = game_id

                        # do something if the game is over
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

            # user updated profile image
            if data.get("image"):
                print(
                    f"[UPLOADING IMAGE]: {active_users[user_id]['username']} ({user_id})"
                )
                size, shape, dtype = (
                    data["image"]["size"],
                    data["image"]["shape"],
                    data["image"]["dtype"],
                )
                if size > max_image_size:
                    error = {"error": "Image too large.", "image_allowed": False}
                    add_to_send_queue(user_id, [pickle.dumps(error)])
                    print(
                        f"[CANCELLED UPLOADING]: {active_users[user_id]['username']} ({user_id})"
                    )

                else:

                    add_to_send_queue(user_id, [pickle.dumps({"image_allowed": True})])

                    full_image = recieve_data(conn)

                    # user disconnected
                    if full_image == "":
                        continue

                    # print("Total bytes recieved: ", len(full_image))

                    print(
                        f"[UPLOADED IMAGE]: {active_users[user_id]['username']} ({user_id})"
                    )

                    profile_pictures[user_id] = {
                        "size": size,
                        "user_id": user_id,
                        "shape": shape,
                        "dtype": dtype,
                        "image": full_image,
                    }

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
                        f"[FINISHED UPLOAD]:  {active_users[user_id]['username']} ({user_id})"
                    )

            # user updated username ro something else
            if data.get("updated"):
                reply.update(update_user(user_id, data["updated"]))

            add_to_send_queue(user_id, [pickle.dumps(reply)])

        except Exception as e:
            print(f"error while processing data from {user_id}", e)
            try:
                print("data recieved was:", data, "length is:", len(data))
            except:
                print("no data recieved from", user_id)
            break

    # the user has disconnected
    disconnect_user(user_id, user_stats)
    # close the connection
    conn.close()


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    # bind the socket to the host address and port
    s.bind((IP, PORT))
    print("Server started at: ", s.getsockname())

    # listen for connections
    s.listen()
    print("Server has started. waiting for connections...")

    while True:
        # accept any connection
        # a connection will come in the form a tuple
        # the connection itself with via the server and the client can communicate
        # and the address from where we are recieving the connection
        conn, addr = s.accept()
        print("[CONNECTED]: ", addr)
        total_connections_so_far += 1  # increment the totoal connections
        # generate a user
        # this cannot be done inside a thread because,
        # if 2 people connect at the same time, there will be an error
        user_id, user_stats = create_user(conn, addr)
        if not user_id:
            continue
        # start a thread for the new client
        start_new_thread(threaded_client, (conn, addr, user_id, user_stats))
        # start a thread to send messages to the new client
        start_new_thread(execute_send_queue, (user_id,))

