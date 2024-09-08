import random
from constants import *

# Class to handle the logic for Tic Tac Toe


class TTT_Logic:
    def __init__(self, player1, player2):
        """
        Initialize the Tic Tac Toe game with two players.

        Args:
        player1 (dict): Dictionary containing player1's information, including 'id'.
        player2 (dict): Dictionary containing player2's information, including 'id'.
        """
        # Initialize player IDs and starting turn
        self.player1_id = player1["id"]
        self.player2_id = player2["id"]
        # Randomly select who starts
        self.turn_id = random.choice([self.player1_id, self.player2_id])
        self.turn_string = "X"  # 'X' starts first
        self.X_id = self.turn_id
        self.O_id = self.player1_id if self.X_id == self.player2_id else self.player2_id

        # Board setup
        self.rows = tic_tac_toe_rows
        self.cols = tic_tac_toe_cols
        self.board = [None for _ in range(
            self.rows * self.cols)]  # Empty board

    def get_identification_dict(self):
        """
        Return a dictionary mapping player IDs to their respective symbols ('X' or 'O').

        Returns:
        dict: Mapping of player IDs to their symbols.
        """
        return {self.X_id: "X", self.O_id: "O"}

    def validate(self, id, move):
        """
        Validate a move for a player.

        Args:
        id (int): Player ID making the move.
        move (int): Position on the board where the player wants to place their symbol.

        Returns:
        tuple: (is_valid (bool), error_message (str or None))
        """
        if not self.turn_id == id:
            return False, "Not your turn!"
        if self.board[move] is not None:
            return False, "Invalid move!"
        return True, None

    def move(self, to):
        """
        Make a move on the board.

        Args:
        to (int): Position on the board where the player wants to place their symbol.

        Returns:
        tuple: (game_over (dict or False), response (dict))
        """
        self.board[to] = self.turn_string  # Place the symbol on the board
        moved_player_id = self.turn_id
        turn_string = self.turn_string

        # Switch turns
        if self.turn_string == "X":
            self.turn_string = "O"
            self.turn_id = self.O_id
        else:
            self.turn_string = "X"
            self.turn_id = self.X_id

        # Prepare response
        r = {}
        r["moved"] = {
            "who": moved_player_id,
            "to": to,
            "turn_string": turn_string,
            "turn_id": self.get_turn_id(),
        }

        return self.check_game_over(), r

    def get_turn_id(self):
        """
        Get the ID of the player whose turn it is.

        Returns:
        int: Player ID whose turn it is.
        """
        return self.turn_id

    def check_game_over(self):
        """
        Check if the game is over by evaluating rows, columns, and diagonals for a win.

        Returns:
        dict or False: If there is a winner, returns a dictionary with 'winner_id' and 'indices'.
                       If the game is a tie, returns {'winner_id': None, 'tie': True}.
                       Otherwise, returns False.
        """
        # Check for a complete row
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

        # Check for a complete column
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

        # Check diagonals (only for square boards)
        if self.rows == self.cols:
            d1 = []  # Diagonal from top left to bottom right
            d2 = []  # Diagonal from top right to bottom left
            for i in range(self.rows):
                d1.append(i * self.cols + i)
                d2.append(i * self.cols + (self.cols - 1 - i))

            for i, ind in enumerate(d1):
                if not self.board[ind] or (
                    i < self.rows -
                        1 and self.board[ind] != self.board[d1[i + 1]]
                ):
                    break
            else:
                return {
                    "winner_id": self.X_id if self.board[d1[0]] == "X" else self.O_id,
                    "indices": d1,
                }

            for i, ind in enumerate(d2):
                if not self.board[ind] or (
                    i < self.rows -
                        1 and self.board[ind] != self.board[d2[i + 1]]
                ):
                    break
            else:
                return {
                    "winner_id": self.X_id if self.board[d2[0]] == "X" else self.O_id,
                    "indices": d2,
                }

        # Check for a tie
        if self.board.count(None) == 0:
            return {"winner_id": None, "tie": True}


# Class to handle the logic for Connect4
class Connect4_Logic:
    def __init__(self, player1, player2):
        """
        Initialize the Connect4 game with two players.

        Args:
        player1 (dict): Dictionary containing player1's information, including 'id'.
        player2 (dict): Dictionary containing player2's information, including 'id'.
        """
        # Initialize player IDs and starting turn
        self.player1_id = player1["id"]
        self.player2_id = player2["id"]
        # Randomly select who starts
        self.turn_id = random.choice([self.player1_id, self.player2_id])
        self.turn_string = "red"  # 'red' starts first
        self.red_id = self.turn_id
        self.blue_id = (
            self.player1_id if self.red_id == self.player2_id else self.player2_id
        )

        # Board setup
        self.rows = connect4_rows
        self.cols = connect4_cols
        self.board = [[None for _ in range(self.cols)]
                      for __ in range(self.rows)]  # Empty board

    def get_identification_dict(self):
        """
        Return a dictionary mapping player IDs to their respective colors ('red' or 'blue').

        Returns:
        dict: Mapping of player IDs to their colors.
        """
        return {self.red_id: "red", self.blue_id: "blue"}

    def validate(self, id, col):
        """
        Validate a move for a player.

        Args:
        id (int): Player ID making the move.
        col (int): Column where the player wants to drop their piece.

        Returns:
        tuple: (is_valid (bool), error_message (str or None))
        """
        if not self.turn_id == id:
            return False, "Not your turn!"

        if self.board[0][col] is not None:
            return False, "Invalid spot!"

        return True, None

    def move(self, col):
        """
        Make a move on the board.

        Args:
        col (int): Column where the player wants to drop their piece.

        Returns:
        tuple: (game_over (dict or False), response (dict))
        """
        moved_row = None
        # Place a piece in the lowest available row for the specified column
        for r in range(self.rows - 1, -1, -1):
            if self.board[r][col] is None:
                moved_row = r
                self.board[r][col] = self.turn_string
                break
        else:
            return False

        moved_player_id = self.turn_id
        turn_string = self.turn_string

        # Switch turns
        if self.turn_string == "red":
            self.turn_string = "blue"
            self.turn_id = self.blue_id
        else:
            self.turn_string = "red"
            self.turn_id = self.red_id

        # Prepare response
        r = {}
        r["moved"] = {
            "who": moved_player_id,
            "to": (moved_row, col),
            "turn_string": turn_string,
            "turn_id": self.get_turn_id(),
        }

        return self.check_game_over(), r

    def get_turn_id(self):
        """
        Get the ID of the player whose turn it is.

        Returns:
        int: Player ID whose turn it is.
        """
        return self.turn_id

    def check_game_over(self):
        """
        Check if the game is over by evaluating rows, columns, and diagonals for a win.

        Returns:
        dict or False: If there is a winner, returns a dictionary with 'winner_id' and 'indices'.
                       If the game is a tie, returns {'winner_id': None, 'tie': True}.
                       Otherwise, returns False.
        """
        # Check for 4 in a row
        for r in range(self.rows):
            for c in range(self.cols):
                if c <= self.cols - connect4_number and self.board[r][c]:
                    indices = [(r, c)]
                    for i in range(1, connect4_number):
                        if self.board[r][c + i] != self.board[r][c]:
                            break
                        indices.append((r, c + i))
                    else:
                        return {"winner_id": self.red_id if self.board[r][c] == "red" else self.blue_id, "indices": indices}

                # Check for 4 in a column
                if r <= self.rows - connect4_number and self.board[r][c]:
                    indices = [(r, c)]
                    for i in range(1, connect4_number):
                        if self.board[r + i][c] != self.board[r][c]:
                            break
                        indices.append((r + i, c))
                    else:
                        return {"winner_id": self.red_id if self.board[r][c] == "red" else self.blue_id, "indices": indices}

                # Check for left-right and top-bottom diagonal
                if r <= self.rows - connect4_number and c <= self.cols - connect4_number and self.board[r][c]:
                    indices = [(r, c)]
                    for i in range(1, connect4_number):
                        if self.board[r + i][c + i] != self.board[r][c]:
                            break
                        indices.append((r + i, c + i))
                    else:
                        return {"winner_id": self.red_id if self.board[r][c] == "red" else self.blue_id, "indices": indices}

                # Check for right-left and top-bottom diagonal
                if r <= self.rows - connect4_number and c >= connect4_number - 1 and self.board[r][c]:
                    indices = [(r, c)]
                    for i in range(1, connect4_number):
                        if self.board[r + i][c - i] != self.board[r][c]:
                            break
                        indices.append((r + i, c - i))
                    else:
                        return {"winner_id": self.red_id if self.board[r][c] == "red" else self.blue_id, "indices": indices}

        # Check for a tie
        for row in self.board:
            if row.count(None) > 0:
                break
        else:
            return {"winner_id": None, "tie": True}

        return False
