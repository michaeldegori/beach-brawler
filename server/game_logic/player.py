class Player:
    def __init__(self, id, position=(0, 0)):
        self.id = id
        self.position = position
        self.health = 100  # Starting Health

    def move(self, direction):
        if direction == 'up':
            self.position = (self.position[0], self.position[1] + 1)
        if direction == 'down':
            self.position = (self.position[0], self.position[1] - 1)
        if direction == 'left':
            self.position = (self.position[0] - 1, self.position[1])
        if direction == 'right':
            self.position = (self.position[0] + 1, self.position[1])

    def attack(self, target_opponent):
        target_opponent.health -= 10

    def reset(self):
        self.position = (0, 0)
        self.health = 100
