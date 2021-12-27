import random
from constants import *

# the logic for tic tac toe
class TTT_Logic:
    def __init__(self, player1, player2):
        # init some vars
        self.player1_id = player1["id"]
        self.player2_id = player2["id"]
        self.turn_id = random.choice([self.player1_id, self.player2_id])
        self.turn_string = "X"
        self.X_id = self.turn_id
        self.O_id = self.player1_id if self.X_id == self.player2_id else self.player2_id
        self.rows = tic_tac_toe_rows
        self.cols = tic_tac_toe_cols
        self.board = [None for _ in range(self.rows * self.cols)]

    # return who is what
    def get_identification_dict(self):
        return {self.X_id: "X", self.O_id: "O"}

    # check if a move is valid
    def validate(self, id, move):
        if not self.turn_id == id:
            return False, "Not your turn!"
        if self.board[move] != None:
            return False, "Invalid move!"
        return True, None

    # place a piece on a location
    def move(self, to):
        self.board[to] = self.turn_string
        moved_player_id = self.turn_id
        turn_string = self.turn_string
        if self.turn_string == "X":
            self.turn_string = "O"
            self.turn_id = self.O_id
        else:
            self.turn_string = "X"
            self.turn_id = self.X_id

        r = {}
        r["moved"] = {
            "who": moved_player_id,
            "to": to,
            "turn_string": turn_string,
            "turn_id": self.get_turn_id(),
        }

        return self.check_game_over(), r

    # whose turn is it
    def get_turn_id(self):
        return self.turn_id

    # check for game over (dynamic!)
    def check_game_over(self):
        # check for a complete row
        for r in range(self.rows):
            winning_indices = []
            for c in range(self.cols):
                if (
                    c < self.cols - 1
                    and self.board[r * self.cols + c]
                    != self.board[c + 1 + self.cols * r]
                ) or self.board[c + self.cols * r] is None:
                    break

                winning_indices.append(c + self.cols * r)
            else:
                return {
                    "winner_id": self.X_id
                    if self.board[r * self.cols + c] == "X"
                    else self.O_id,
                    "indices": winning_indices,
                }

        # check for a complete colmn
        for c in range(self.cols):
            winning_indices = []
            for r in range(self.rows):
                if (
                    r < self.rows - 1
                    and self.board[c + self.cols * r]
                    != self.board[c + self.cols * (r + 1)]
                ) or self.board[c + self.cols * r] is None:
                    break

                winning_indices.append(c + self.cols * r)

            else:
                return {
                    "winner_id": self.X_id
                    if self.board[c + self.cols * r] == "X"
                    else self.O_id,
                    "indices": winning_indices,
                }

        # check for diagonals, but only if the game board is square
        if self.rows == self.cols:
            d1 = []  # diagonal from top left to botton right
            d2 = []  # diagonal from top right to bottom left
            for i in range(self.rows):
                d1.append(i * self.cols + i)
                d2.append(i * self.cols + (self.cols - 1 - i))

            for i, ind in enumerate(d1):
                if not self.board[ind] or (
                    i < self.rows - 1 and self.board[ind] != self.board[d1[i + 1]]
                ):
                    break
            else:
                return {
                    "winner_id": self.X_id if self.board[d1[0]] == "X" else self.O_id,
                    "indices": d1,
                }

            for i, ind in enumerate(d2):
                if not self.board[ind] or (
                    i < self.rows - 1 and self.board[ind] != self.board[d2[i + 1]]
                ):
                    break
            else:
                return {
                    "winner_id": self.X_id if self.board[d2[0]] == "X" else self.O_id,
                    "indices": d2,
                }

        # it is a tie
        if self.board.count(None) == 0:
            return {"winner_id": None, "tie": True}


class Connect4_Logic:
    def __init__(self, player1, player2):
        # init some vars
        self.player1_id = player1["id"]
        self.player2_id = player2["id"]
        self.turn_id = random.choice([self.player1_id, self.player2_id])
        self.turn_string = "red"
        self.red_id = self.turn_id
        self.blue_id = (
            self.player1_id if self.red_id == self.player2_id else self.player2_id
        )
        self.rows = connect4_rows
        self.cols = connect4_cols
        self.board = [[None for _ in range(self.cols)] for __ in range(self.rows)]

    # return who is what
    def get_identification_dict(self):
        return {self.red_id: "red", self.blue_id: "blue"}

    # check if a move is valid
    def validate(self, id, col):
        if not self.turn_id == id:
            return False, "Not your turn!"

        if self.board[0][col] is not None:
            return False, "Invalid spot!"

        return True, None

    # place a piece on a location
    def move(self, col):
        moved_row = None
        # place a coin in the highest row possible for that column
        for r in range(self.rows - 1, -1, -1):
            if self.board[r][col] is None:
                moved_row = r
                self.board[r][col] = self.turn_string
                break
        else:
            return False

        moved_player_id = self.turn_id
        turn_string = self.turn_string

        if self.turn_string == "red":
            self.turn_string = "blue"
            self.turn_id = self.blue_id
        else:
            self.turn_string = "red"
            self.turn_id = self.red_id

        r = {}
        r["moved"] = {
            "who": moved_player_id,
            "to": (moved_row, col),
            "turn_string": turn_string,
            "turn_id": self.get_turn_id(),
        }

        return self.check_game_over(), r

    # whose turn is it
    def get_turn_id(self):
        return self.turn_id

    # check for game over (dynamic!)
    def check_game_over(self):
        for r in range(self.rows):
            for c in range(self.cols):
                # check for 4 in a row
                if c <= self.cols - connect4_number and self.board[r][c]:
                    indices = [(r, c)]
                    for i in range(1, connect4_number):
                        if self.board[r][c + i] != self.board[r][c]:
                            break
                        indices.append((r, c + i))
                    else:
                        # found 4 same coins in a row
                        winner_id = (
                            self.red_id if self.board[r][c] == "red" else self.blue_id
                        )
                        return {"winner_id": winner_id, "indices": indices}

                # check for 4 in a column
                if r <= self.rows - connect4_number and self.board[r][c]:
                    indices = [(r, c)]
                    for i in range(1, connect4_number):
                        if self.board[r + i][c] != self.board[r][c]:
                            break
                        indices.append((r + i, c))
                    else:
                        # found 4 same coins in a column
                        winner_id = (
                            self.red_id if self.board[r][c] == "red" else self.blue_id
                        )
                        return {"winner_id": winner_id, "indices": indices}

                # check for left-right and top-bottom diagonal
                if (
                    r <= self.rows - connect4_number
                    and c <= self.cols - connect4_number
                    and self.board[r][c]
                ):
                    indices = [(r, c)]
                    for i in range(1, connect4_number):
                        if self.board[r + i][c + i] != self.board[r][c]:
                            break
                        indices.append((r + i, c + i))
                    else:
                        # found 4 same coins in the diagonal
                        winner_id = (
                            self.red_id if self.board[r][c] == "red" else self.blue_id
                        )
                        return {"winner_id": winner_id, "indices": indices}

                # check for right-left and top-bottom diagonal
                if (
                    r <= self.rows - connect4_number
                    and c >= connect4_number - 1
                    and self.board[r][c]
                ):
                    indices = [(r, c)]
                    for i in range(1, connect4_number):
                        if self.board[r + i][c - i] != self.board[r][c]:
                            break
                        indices.append((r + i, c - i))
                    else:
                        # found 4 same coins in the diagonal
                        winner_id = (
                            self.red_id if self.board[r][c] == "red" else self.blue_id
                        )
                        return {"winner_id": winner_id, "indices": indices}

        # it is a tie
        for row in self.board:
            if row.count(None) > 0:
                break
        else:
            return {"winner_id": None, "tie": True}

        return False

