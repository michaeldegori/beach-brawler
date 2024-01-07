class Player:
    def __init__(self, id, position=(0, 0)):
        self.id = id
        self.position = position
        self.last_known_position = position
        self.health = 100
        self.is_moving = False
        self.direction = None
        self.speed = 10
        self.vertical_velocity = 0
        self.gravity = 4
        self.jump_strength = 30

    def start_moving(self, direction):
        self.is_moving = True
        self.direction = direction

    def stop_moving(self):
        self.is_moving = False
        self.direction = None

    def update(self):
        self.move()
        self.apply_gravity()

    def move(self):
        x_delta = 0
        if self.is_moving and self.direction:
            if self.direction == 'left':
                x_delta = -self.speed
            elif self.direction == 'right':
                x_delta = self.speed

            # Only update the x position
            self.position = (self.position[0] + x_delta, self.position[1])

    def apply_gravity(self):
        # Update the y position based on the current vertical velocity.
        self.position = (self.position[0], self.position[1] + self.vertical_velocity)

        # If the player is in the air, apply gravity.
        if self.position[1] < 318 or self.vertical_velocity < 0:
            self.vertical_velocity += self.gravity  # Simulate gravity

        # If the player is on the ground, reset the vertical velocity.
        if self.position[1] >= 318:
            self.position = (self.position[0], 318)
            self.vertical_velocity = 0

    def jump(self):
        # Only allow the player to jump if they are on the ground
        if self.position[1] >= 318 and self.vertical_velocity == 0:
            self.vertical_velocity = -self.jump_strength  # Adjust as needed for the jump strength

    def attack(self, target_opponent):
        target_opponent.health -= 10

    def reset(self):
        self.position = (0, 0)
        self.last_known_position = self.position
        self.health = 100
        self.vertical_velocity = 0
        self.is_moving = False
        self.direction = None
