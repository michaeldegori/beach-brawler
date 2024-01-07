class Player:
    def __init__(self, id, position=(0, 0)):
        self.id = id
        self.position = position
        self.last_known_position = position
        self.health = 100
        self.vertical_velocity = 0
        self.is_moving = False
        self.direction = None
        self.speed = 10

    def jump(self):
        if self.vertical_velocity == 0:
            self.vertical_velocity = -25

    def start_moving(self, direction):
        self.is_moving = True
        self.direction = direction

    def stop_moving(self):
        self.is_moving = False
        self.direction = None

    def move(self):
        if self.is_moving and self.direction:
            self.last_known_position = self.position

            if self.direction == 'left':
                self.position = (self.position[0] - self.speed, self.position[1])
            elif self.direction == 'right':
                self.position = (self.position[0] + self.speed, self.position[1])

    def update(self):
        self.move()
        self.apply_gravity()

    def apply_gravity(self):
        # TODO: Gravity logic
        pass

    def attack(self, target_opponent):
        target_opponent.health -= 10

    def reset(self):
        self.position = (0, 0)
        self.last_known_position = self.position
        self.health = 100
        self.vertical_velocity = 0
        self.is_moving = False
        self.direction = None
