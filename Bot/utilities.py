import random


# the tic tac toe board
class TTT_Board:
    def __init__(
        self, game_id, curr_user_id, X_id, O_id, move, turn_id, rows=3, cols=3,
    ):
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

        if self.turn_id == self.curr_user_id:
            self.move_req(self.game_id, random.randint(0, self.rows * self.cols - 1))

    def generate_board(self):
        for i in range(self.rows):
            self.board.append([])
            for j in range(self.cols):
                self.board[i].append(None)

    def move(self):
        # AI to make its turn
        best_score = -float("inf")
        best_move = None

        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c] is None:
                    self.board[r][c] = self.user_text

                    # now itll be humans turn
                    score = self.minimax(0, False, self.opp_text, ["X", "O"],)

                    self.board[r][c] = None

                    if score > best_score:
                        best_score = score
                        best_move = (r, c)

        self.move_req(self.game_id, self.cols * best_move[0] + best_move[1])
        self.turn = self.opp_text
        self.turn_id = self.opp_id

    def place(self, data):
        id = data["to"]  # index for the 1d array
        # but our array is 2d, so convert it to 2d
        r, c = id // self.cols, id % self.cols
        text = data["turn_string"]

        # print(f"[{'BOT'}]: {text}({data['who']}) moved in TTT to {id}")
        self.board[r][c] = text

        self.turn_id = data["turn_id"]
        self.turn = "X" if self.turn_id == self.X_id else "O"
        if self.turn_id == self.curr_user_id:
            self.move()

    # check for game over (dynamic!)
    def check_game_over(self):
        # check for a complete row
        for r in range(self.rows):
            if len(set(self.board[r])) == 1 and self.board[r][0] is not None:
                return self.board[r][0]

        # check for a complete column
        for c in range(self.cols):
            col = set([self.board[r][c] for r in range(self.rows)])
            if len(col) == 1 and self.board[0][c] is not None:
                return self.board[0][c]

        # check for diagonals, but only if the game board is square
        if self.rows == self.cols:
            d1 = []  # diagonal from top left to botton right
            d2 = []  # diagonal from top right to bottom left
            for r in range(self.rows):
                d1.append(self.board[r][r])
                d2.append(self.board[r][self.rows - r - 1])

            if len(set(d1)) == 1 and d1[0] is not None:
                return d1[0]

            if len(set(d2)) == 1 and d2[0] is not None:
                return d2[0]

        # it is a tie
        none_count = 0
        for row in self.board:
            none_count += row.count(None)
        if none_count == 0:
            return "tie"

        return None  # game is not done yet

    def game_over_protocol(self, indices, winner_id, *args):
        print(f"[BOT]: GAME OVER {winner_id} won!")

    def minimax(
        self, depth, is_maximizing, turn, turns=["X", "O"],
    ):

        result = self.check_game_over()

        # terminal case, game is over so return the score corresponding to the player who won
        if result is not None:
            return self.scores[result]

        next_turn = turns[1] if turn == turns[0] else turns[0]

        # it is this players turn, we need to try and get the maximum score
        if is_maximizing:
            best_score = -float("inf")

            for r in range(self.rows):
                for c in range(self.cols):
                    if self.board[r][c] is None:
                        self.board[r][c] = turn
                        score = self.minimax(depth + 1, False, next_turn, turns,)
                        self.board[r][c] = None
                        best_score = max(score, best_score)

            return best_score

        # the human player will make a move with the least socre, i.e the best move possible for him
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


# the connect4 board
class Connect4_Board:
    def __init__(
        self, game_id, curr_player_id, red_id, blue_id, move, turn_id, rows=12, cols=13,
    ):
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

        # the board - None is open, red is filled with red coin, and blue is filled with blue coin
        self.board = [[None for c in range(self.cols)] for r in range(self.rows)]

        self.move_req = move

        # variable to control the animating coin, when some one wins
        self.game_over = False
        self.winning_indices = []

        if self.turn_id == self.curr_user_id:
            self.move_req(self.game_id, random.randint(0, self.cols - 1))

    def get_top_row(self, col):
        # place a coin in the highest row possible for that column
        for r in range(self.rows - 1, -1, -1):
            if self.board[r][col] is None:
                return r

    def minimax(self, depth, is_maximizing, turn, turns=["red", "blue"]):

        if depth > 5:
            return 0

        result = self.check_game_over()

        # terminal case, game is over so return the score corresponding to the player who won
        if result is not None:
            return self.scores[result]

        next_turn = turns[1] if turn == turns[0] else turns[0]

        # it is this players turn, we need to try and get the maximum score
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

        # the human player will make a move with the least socre, i.e the best move possible for him
        else:
            best_score = float("inf")

            for c in range(self.cols):
                r = self.get_top_row(c)
                if r is not None:
                    self.board[r][c] = turn
                    score = self.minimax(depth + 1, True, next_turn, turns,)
                    self.board[r][c] = None
                    best_score = min(score, best_score)

            return best_score

    def move(self):
        # AI to make its turn
        best_score = -float("inf")
        best_move = None

        for c in range(self.cols):
            if self.board[0][c] is None:
                row = self.get_top_row(c)
                if row is not None:
                    self.board[row][c] = self.player_color

                    # humans turn
                    score = self.minimax(0, False, self.opp_color, ["red", "blue"],)

                    self.board[row][c] = None

                    if score > best_score:
                        best_score = score
                        best_move = c

        self.move_req(self.game_id, best_move)

    def check_game_over(self):
        for r in range(self.rows):
            for c in range(self.cols):
                # check for 4 in a row
                if c <= self.cols - self.connect_number and self.board[r][c]:
                    indices = [(r, c)]
                    for i in range(1, self.connect_number):
                        if self.board[r][c + i] != self.board[r][c]:
                            break
                        indices.append((r, c + i))
                    else:
                        # found 4 same coins in a row
                        return self.board[r][c]

                # check for 4 in a column
                if r <= self.rows - self.connect_number and self.board[r][c]:
                    indices = [(r, c)]
                    for i in range(1, self.connect_number):
                        if self.board[r + i][c] != self.board[r][c]:
                            break
                        indices.append((r + i, c))
                    else:
                        # found 4 same coins in a column
                        return self.board[r][c]

                # check for left-right and top-bottom diagonal
                if (
                    r <= self.rows - self.connect_number
                    and c <= self.cols - self.connect_number
                    and self.board[r][c]
                ):
                    indices = [(r, c)]
                    for i in range(1, self.connect_number):
                        if self.board[r + i][c + i] != self.board[r][c]:
                            break
                        indices.append((r + i, c + i))
                    else:
                        # found 4 same coins in the diagonal
                        return self.board[r][c]

                # check for right-left and top-bottom diagonal
                if (
                    r <= self.rows - self.connect_number
                    and c >= self.connect_number - 1
                    and self.board[r][c]
                ):
                    indices = [(r, c)]
                    for i in range(1, self.connect_number):
                        if self.board[r + i][c - i] != self.board[r][c]:
                            break
                        indices.append((r + i, c - i))
                    else:
                        # found 4 same coins in the diagonal
                        return self.board[r][c]

        # it is a tie
        for row in self.board:
            if row.count(None) > 0:
                break
        else:
            return "tie"

        return None

    # what happens when the game ends?
    def game_over_protocol(self, indices, winner_id, *args):
        print(f"[BOT]: GAME OVER {winner_id} won!")

    # place a coin in the desired location
    def place(self, data):
        to = data["to"]  # (row,col)
        text = data["turn_string"]
        self.board[to[0]][to[1]] = text

        self.turn_id = data["turn_id"]
        self.turn = "red" if self.turn_id == self.red_id else "blue"

        if self.turn_id == self.curr_user_id:
            self.move()

