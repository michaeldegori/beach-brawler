class Player:
    def __init__(self, id, position=(0, 0)):
        self.id = id
        self.position = position
        self.health = 100
        self.vertical_velocity = 0

    def jump(self):
        if self.vertical_velocity == 0:
            self.vertical_velocity = -25

    def move(self, direction):
        if direction == 'left':
            self.position = (self.position[0] - 1, self.position[1])
        if direction == 'right':
            self.position = (self.position[0] + 1, self.position[1])

    def attack(self, target_opponent):
        target_opponent.health -= 10

    def reset(self):
        self.position = (0, 0)
        self.health = 100
