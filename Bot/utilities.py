import random
# Class to represent the Tic Tac Toe board


class TTT_Board:
    def __init__(
        self, game_id, curr_user_id, X_id, O_id, move, turn_id, rows=3, cols=3,
    ):
        """
        Initialize the Tic Tac Toe board.
        """
        self.game_id = game_id
        self.curr_user_id = curr_user_id
        self.X_id, self.O_id = X_id, O_id
        self.opp_id = self.X_id if self.O_id == self.curr_user_id else self.O_id
        self.user_text = "X" if self.curr_user_id == self.X_id else "O"
        self.opp_text = "X" if self.user_text == "O" else "O"
        self.turn_id = turn_id
        self.turn = "X" if self.X_id == self.turn_id else "O"
        self.rows, self.cols = rows, cols
        self.board = []
        self.move_req = move
        self.scores = {self.user_text: 1, self.opp_text: -1, "tie": 0}
        self.generate_board()

        # Make an initial move if it's the current user's turn
        if self.turn_id == self.curr_user_id:
            self.move_req(self.game_id, random.randint(
                0, self.rows * self.cols - 1))

    def generate_board(self):
        """Create an empty board."""
        for i in range(self.rows):
            self.board.append([None] * self.cols)

    def move(self):
        """Determine and make the best move using minimax."""
        best_score = -float("inf")
        best_move = None

        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c] is None:
                    self.board[r][c] = self.user_text
                    score = self.minimax(0, False, self.opp_text, ["X", "O"])
                    self.board[r][c] = None
                    if score > best_score:
                        best_score = score
                        best_move = (r, c)

        # Request the best move
        self.move_req(self.game_id, self.cols * best_move[0] + best_move[1])
        self.turn = self.opp_text
        self.turn_id = self.opp_id

    def place(self, data):
        """Place a move on the board."""
        id = data["to"]
        r, c = id // self.cols, id % self.cols
        text = data["turn_string"]
        self.board[r][c] = text
        self.turn_id = data["turn_id"]
        self.turn = "X" if self.turn_id == self.X_id else "O"
        if self.turn_id == self.curr_user_id:
            self.move()

    def check_game_over(self):
        """Check if the game has ended."""
        # Check rows
        for r in range(self.rows):
            if len(set(self.board[r])) == 1 and self.board[r][0] is not None:
                return self.board[r][0]

        # Check columns
        for c in range(self.cols):
            col = set([self.board[r][c] for r in range(self.rows)])
            if len(col) == 1 and self.board[0][c] is not None:
                return self.board[0][c]

        # Check diagonals (only if board is square)
        if self.rows == self.cols:
            d1 = [self.board[r][r] for r in range(self.rows)]
            d2 = [self.board[r][self.rows - r - 1] for r in range(self.rows)]
            if len(set(d1)) == 1 and d1[0] is not None:
                return d1[0]
            if len(set(d2)) == 1 and d2[0] is not None:
                return d2[0]

        # Check for tie
        none_count = sum(row.count(None) for row in self.board)
        if none_count == 0:
            return "tie"

        return None

    def game_over_protocol(self, indices, winner_id, *args):
        """Handle end-of-game protocol."""
        print(f"[BOT]: GAME OVER {winner_id} won!")

    def minimax(
        self, depth, is_maximizing, turn, turns=["X", "O"],
    ):
        """Minimax algorithm for best move calculation."""
        result = self.check_game_over()
        if result is not None:
            return self.scores[result]

        next_turn = turns[1] if turn == turns[0] else turns[0]

        if is_maximizing:
            best_score = -float("inf")
            for r in range(self.rows):
                for c in range(self.cols):
                    if self.board[r][c] is None:
                        self.board[r][c] = turn
                        score = self.minimax(
                            depth + 1, False, next_turn, turns)
                        self.board[r][c] = None
                        best_score = max(score, best_score)
            return best_score
        else:
            best_score = float("inf")
            for r in range(self.rows):
                for c in range(self.cols):
                    if self.board[r][c] is None:
                        self.board[r][c] = turn
                        score = self.minimax(depth + 1, True, next_turn, turns)
                        self.board[r][c] = None
                        best_score = min(score, best_score)
            return best_score


# Class to represent the Connect4 board
class Connect4_Board:
    def __init__(
        self, game_id, curr_player_id, red_id, blue_id, move, turn_id, rows=12, cols=13,
    ):
        """
        Initialize the Connect4 board.
        """
        self.game_id = game_id
        self.curr_user_id = curr_player_id
        self.red_id, self.blue_id = red_id, blue_id
        self.opp_id = self.red_id if self.curr_user_id == self.blue_id else self.blue_id
        self.player_color = "red" if self.red_id == curr_player_id else "blue"
        self.opp_color = "red" if self.player_color == "blue" else "blue"
        self.turn_id = turn_id
        self.turn = "red" if self.turn_id == self.red_id else "blue"
        self.scores = {self.player_color: 1, self.opp_color: -1, "tie": 0}
        self.rows, self.cols = rows, cols
        self.connect_number = 4
        self.board = [[None for _ in range(self.cols)]
                      for _ in range(self.rows)]
        self.move_req = move
        self.game_over = False
        self.winning_indices = []

        # Make an initial move if it's the current player's turn
        if self.turn_id == self.curr_user_id:
            self.move_req(self.game_id, random.randint(0, self.cols - 1))

    def get_top_row(self, col):
        """Find the highest open row in the specified column."""
        for r in range(self.rows - 1, -1, -1):
            if self.board[r][col] is None:
                return r

    def minimax(self, depth, is_maximizing, turn, turns=["red", "blue"]):
        """Minimax algorithm for best move calculation."""
        if depth > 5:
            return 0

        result = self.check_game_over()
        if result is not None:
            return self.scores[result]

        next_turn = turns[1] if turn == turns[0] else turns[0]

        if is_maximizing:
            best_score = -float("inf")
            for c in range(self.cols):
                r = self.get_top_row(c)
                if r is not None:
                    self.board[r][c] = turn
                    score = self.minimax(depth + 1, False, next_turn, turns)
                    self.board[r][c] = None
                    best_score = max(score, best_score)
            return best_score
        else:
            best_score = float("inf")
            for c in range(self.cols):
                r = self.get_top_row(c)
                if r is not None:
                    self.board[r][c] = turn
                    score = self.minimax(depth + 1, True, next_turn, turns)
                    self.board[r][c] = None
                    best_score = min(score, best_score)
            return best_score

    def move(self):
        """Determine and make the best move using minimax."""
        best_score = -float("inf")
        best_move = None

        for c in range(self.cols):
            if self.board[0][c] is None:
                row = self.get_top_row(c)
                if row is not None:
                    self.board[row][c] = self.player_color
                    score = self.minimax(
                        0, False, self.opp_color, ["red", "blue"])
                    self.board[row][c] = None
                    if score > best_score:
                        best_score = score
                        best_move = c

        # Request the best move
        self.move_req(self.game_id, best_move)

    def check_game_over(self):
        """Check if the game has ended."""
        for r in range(self.rows):
            for c in range(self.cols):
                # Check horizontal
                if c <= self.cols - self.connect_number and self.board[r][c]:
                    indices = [(r, c)]
                    for i in range(1, self.connect_number):
                        if self.board[r][c + i] == self.board[r][c]:
                            indices.append((r, c + i))
                        else:
                            break
                    if len(indices) == self.connect_number:
                        self.winning_indices = indices
                        return self.board[r][c]

                # Check vertical
                if r <= self.rows - self.connect_number and self.board[r][c]:
                    indices = [(r, c)]
                    for i in range(1, self.connect_number):
                        if self.board[r + i][c] == self.board[r][c]:
                            indices.append((r + i, c))
                        else:
                            break
                    if len(indices) == self.connect_number:
                        self.winning_indices = indices
                        return self.board[r][c]

                # Check diagonal down-right
                if r <= self.rows - self.connect_number and c <= self.cols - self.connect_number and self.board[r][c]:
                    indices = [(r, c)]
                    for i in range(1, self.connect_number):
                        if self.board[r + i][c + i] == self.board[r][c]:
                            indices.append((r + i, c + i))
                        else:
                            break
                    if len(indices) == self.connect_number:
                        self.winning_indices = indices
                        return self.board[r][c]

                # Check diagonal up-right
                if r >= self.connect_number - 1 and c <= self.cols - self.connect_number and self.board[r][c]:
                    indices = [(r, c)]
                    for i in range(1, self.connect_number):
                        if self.board[r - i][c + i] == self.board[r][c]:
                            indices.append((r - i, c + i))
                        else:
                            break
                    if len(indices) == self.connect_number:
                        self.winning_indices = indices
                        return self.board[r][c]

        if all(self.board[0][c] is not None for c in range(self.cols)):
            return "tie"

        return None

    def game_over_protocol(self, indices, winner_id, *args):
        """Handle end-of-game protocol."""
        print(f"[BOT]: GAME OVER {winner_id} won!")

    def place(self, data):
        """Place a move on the board."""
        col = data["to"]
        row = self.get_top_row(col)
        color = data["turn_string"]
        self.board[row][col] = color
        if self.turn_id == self.red_id:
            self.turn = "blue"
        else:
            self.turn = "red"
        if self.turn_id == self.curr_user_id:
            self.move()
