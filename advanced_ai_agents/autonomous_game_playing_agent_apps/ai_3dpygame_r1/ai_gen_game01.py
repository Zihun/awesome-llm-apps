import pygame
import sys
import math

# Initialize pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)

# Screen setup
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("3D Maze Game")

# 3D Maze structure
MAZE = [
    [[1, 0, 1], [1, 1, 1], [0, 1, 0]],
    [[0, 1, 0], [1, 0, 1], [1, 1, 1]],
    [[1, 1, 1], [1, 0, 1], [1, 0, 1]]
]

# Player properties
player_pos = [0, 0]
player_layer = 0
player_size = 20

# Perspective projection parameters
fov = math.pi / 3
half_fov = fov / 2
dist = (WIDTH // 2) / math.tan(half_fov)
H_PROJECTION = (WIDTH // 2) / math.tan(half_fov)

# Function to draw a cube
def draw_cube(column, row, scale, offset):
    points = [
        (column * scale[0] + offset[0], row * scale[1] + offset[1]),
        ((column + 1) * scale[0] + offset[0], row * scale[1] + offset[1]),
        ((column + 1) * scale[0] + offset[0], (row + 1) * scale[1] + offset[1]),
        (column * scale[0] + offset[0], (row + 1) * scale[1] + offset[1])
    ]
    pygame.draw.lines(screen, BLUE, True, points, 2)

# Function to draw maze layer
def draw_layer(layer, scale, offset):
    for col in range(len(MAZE[layer])):
        for row in range(len(MAZE[layer][col])):
            if MAZE[layer][col][row] == 1:
                draw_cube(col, row, scale, offset)

# Main game loop
clock = pygame.time.Clock()
while True:
    screen.fill(BLACK)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP and player_pos[0] > 0:
                player_pos[0] -= 1
            elif event.key == pygame.K_DOWN and player_pos[0] < len(MAZE[player_layer]) - 1:
                player_pos[0] += 1
            elif event.key == pygame.K_LEFT and player_pos[1] > 0:
                player_pos[1] -= 1
            elif event.key == pygame.K_RIGHT and player_pos[1] < len(MAZE[player_layer][0]) - 1:
                player_pos[1] += 1
            elif event.key == pygame.K_SPACE:
                player_layer = (player_layer + 1) % len(MAZE)

    # Draw maze
    scale = (WIDTH // 3, HEIGHT // 3)
    offset = ((WIDTH - scale[0] * len(MAZE[0])), (HEIGHT - scale[1] * len(MAZE[0][0]))) // 2
    draw_layer(player_layer, scale, offset)

    # Draw player
    pygame.draw.circle(screen, GREEN, (player_pos[1] * scale[0] + offset[0] + scale[0] // 2, player_pos[0] * scale[1] + offset[1] + scale[1] // 2), player_size)

    pygame.display.flip()
    clock.tick(30)