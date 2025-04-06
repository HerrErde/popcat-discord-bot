import os
import random
import time

# Define the screen dimensions
SCREEN_WIDTH = 20
SCREEN_HEIGHT = 3

# Define the Dino and obstacle properties
DINO_START_POS = [5, SCREEN_HEIGHT - 2]  # Dino's initial position
OBSTACLE_CHAR = ":cactus: "
DINO_CHAR = ":t_rex:"
EMPTY_CHAR = "-"

# Game parameters
OBSTACLE_FREQUENCY = 0.2  # Frequency of new obstacles
OBSTACLE_GAP = 10  # Minimum gap between obstacles
FLOOR_LEVEL = SCREEN_HEIGHT - 2  # Floor level for the Dino


class DinoGame:
    def __init__(self):
        self.dino_pos = list(DINO_START_POS)
        self.obstacles = []
        self.jump = False
        self.jump_height = 2
        self.jump_duration = 0.2
        self.jump_counter = 0

    def clear_screen(self):
        os.system("cls" if os.name == "nt" else "clear")

    def create_obstacle(self):
        if not self.obstacles or self.obstacles[-1][0] < SCREEN_WIDTH - OBSTACLE_GAP:
            if random.random() < OBSTACLE_FREQUENCY:
                self.obstacles.append([SCREEN_WIDTH - 1, FLOOR_LEVEL])

    def move_obstacles(self):
        for obs in self.obstacles:
            obs[0] -= 1
        self.obstacles = [obs for obs in self.obstacles if obs[0] > 0]

    def draw(self):
        screen = [
            [EMPTY_CHAR for _ in range(SCREEN_WIDTH)] for _ in range(SCREEN_HEIGHT)
        ]

        # Draw the Dino
        screen[self.dino_pos[1]][self.dino_pos[0]] = DINO_CHAR

        # Draw obstacles
        for obs in self.obstacles:
            screen[obs[1]][obs[0]] = OBSTACLE_CHAR

        self.clear_screen()
        for row in screen:
            print("".join(row))

    def update_dino(self):
        if self.jump:
            if self.jump_counter < self.jump_height:
                self.dino_pos[1] -= 1
            elif self.jump_counter < 2 * self.jump_height:
                self.dino_pos[1] += 1
            else:
                self.jump = False
                self.jump_counter = 0
            self.jump_counter += 1

        if self.dino_pos[1] > FLOOR_LEVEL:
            self.dino_pos[1] = FLOOR_LEVEL

    def check_collision(self):
        for obs in self.obstacles:
            if obs[0] == self.dino_pos[0] and obs[1] == self.dino_pos[1]:
                return True
        return False

    def game_loop(self):
        try:
            while True:
                self.create_obstacle()
                self.move_obstacles()
                self.update_dino()

                if self.check_collision():
                    print("Game Over!")
                    break

                # Trigger jump if obstacle is close
                for obs in self.obstacles:
                    if obs[0] == self.dino_pos[0] + 1:
                        self.jump = True

                self.draw()
                time.sleep(self.jump_duration)
        except KeyboardInterrupt:
            self.clear_screen()
            print("Game interrupted. Exiting...")


if __name__ == "__main__":
    game = DinoGame()
    game.game_loop()
