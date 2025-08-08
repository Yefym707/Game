import random
import sys

BOARD_SIZE = 10
NUM_ZOMBIES = 5

class Entity:
    def __init__(self, x, y, symbol):
        self.x = x
        self.y = y
        self.symbol = symbol

class Game:
    def __init__(self):
        self.board_size = BOARD_SIZE
        self.player = Entity(self.board_size // 2, self.board_size // 2, '@')
        self.zombies = []
        self.health = 10
        self.spawn_zombies(NUM_ZOMBIES)

    def spawn_zombies(self, count):
        for _ in range(count):
            while True:
                x = random.randrange(self.board_size)
                y = random.randrange(self.board_size)
                if (x, y) != (self.player.x, self.player.y):
                    self.zombies.append(Entity(x, y, 'Z'))
                    break

    def draw_board(self):
        board = [['.' for _ in range(self.board_size)] for _ in range(self.board_size)]
        board[self.player.y][self.player.x] = self.player.symbol
        for z in self.zombies:
            board[z.y][z.x] = z.symbol
        print("Health:", self.health)
        for row in board:
            print(' '.join(row))

    def move_player(self, direction):
        dx, dy = 0, 0
        if direction == 'w':
            dy = -1
        elif direction == 's':
            dy = 1
        elif direction == 'a':
            dx = -1
        elif direction == 'd':
            dx = 1
        else:
            return
        nx = self.player.x + dx
        ny = self.player.y + dy
        if 0 <= nx < self.board_size and 0 <= ny < self.board_size:
            self.player.x = nx
            self.player.y = ny

    def move_zombies(self):
        for z in self.zombies:
            dx = 0 if z.x == self.player.x else (1 if z.x < self.player.x else -1)
            dy = 0 if z.y == self.player.y else (1 if z.y < self.player.y else -1)
            z.x += dx
            z.y += dy
            if z.x == self.player.x and z.y == self.player.y:
                self.health -= 1
                print("A zombie bites you! Health now", self.health)

    def check_game_over(self):
        return self.health <= 0

    def run(self):
        print("Survive as long as you can. Move with WASD. Ctrl+C to quit.")
        try:
            while not self.check_game_over():
                self.draw_board()
                move = input("Your move (w/a/s/d): ").strip().lower()
                self.move_player(move)
                self.move_zombies()
            print("You have been overwhelmed by zombies!")
        except (KeyboardInterrupt, EOFError):
            print("\nThanks for playing!")


if __name__ == "__main__":
    Game().run()
