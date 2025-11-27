import nuke, math, random
from PySide2.QtCore import QTimer, Qt, QObject
from PySide2.QtGui import QKeyEvent
from PySide2.QtWidgets import QApplication

# Helper: Convert an (R,G,B) tuple into an integer for Nuke’s tile_color (ARGB with alpha=255)
def color_to_nuke(r, g, b):
    return (255 << 24) | (r << 16) | (g << 8) | b

class Game:
    def __init__(self):
        # Grid parameters (80x60 dots, reduced spacing)
        self.WIDTH = 80
        self.HEIGHT = 60
        self.PIXEL_SIZE = 10

        total_width = self.WIDTH * self.PIXEL_SIZE
        total_height = self.HEIGHT * self.PIXEL_SIZE
        margin = 50  # backdrop margin
        
        # Create a backdrop node that encloses the dots area (with extra margin)
        self.backdrop = nuke.createNode("BackdropNode", inpanel=False)
        backdrop_x = -margin // 2
        backdrop_y = -margin // 2
        self.backdrop.setXpos(backdrop_x)
        self.backdrop.setYpos(backdrop_y)
        self.backdrop["bdwidth"].setValue(total_width + margin)
        self.backdrop["bdheight"].setValue(total_height + margin)
        self.backdrop["label"].setValue("Monsters Defeated: 0")
        self.backdrop.setName("Game_Backdrop")

        # Build an 80x60 grid of Dot nodes.
        self.grid_nodes = []
        for row in range(self.HEIGHT):
            grid_row = []
            for col in range(self.WIDTH):
                dot = nuke.createNode("Dot", inpanel=False)
                dot.setXpos(col * self.PIXEL_SIZE)
                dot.setYpos(row * self.PIXEL_SIZE)
                dot["hide_input"].setValue(True)
                grid_row.append(dot)
            self.grid_nodes.append(grid_row)

        # Map data: a fixed, small map (20x8) where walls ('1') bound open space ('.')
        self.map_data = [
            "11111111111111111111",
            "1.................11",
            "1.................11",
            "1.................11",
            "1.................11",
            "1.................11",
            "1.................11",
            "11111111111111111111",
        ]
        self.map_width = len(self.map_data[0])
        self.map_height = len(self.map_data)

        # Environmental objects (e.g., trees) with positions.
        self.environment_objects = [
            {'type': 'tree', 'x': 5.0, 'y': 2.0},
            {'type': 'tree', 'x': 12.0, 'y': 4.0},
            {'type': 'tree', 'x': 16.0, 'y': 2.0},
        ]

        # Player state.
        self.player_x = 3.0
        self.player_y = 3.0
        self.player_angle = 0.0  # 0 radians means facing right.
        self.FOV = math.pi / 4

        # Count of monsters defeated.
        self.monsters_defeated = 0

        # Default pointer color is white.
        self.pointer_color = (255, 255, 255)

        # Start with a few monsters.
        self.monsters = []
        self.spawn_monster(initial=True)
        self.spawn_monster(initial=True)
        self.spawn_monster(initial=True)

        # Set up the game loop timer (~20 frames per second).
        self.timer = QTimer()
        self.timer.timeout.connect(self.game_loop)
        self.timer.start(50)

    # Simple raycaster: cast a ray until a wall is hit.
    def cast_ray(self, ray_angle):
        ray_x = self.player_x
        ray_y = self.player_y
        step = 0.05
        while True:
            ray_x += math.cos(ray_angle) * step
            ray_y += math.sin(ray_angle) * step
            map_x = int(ray_x)
            map_y = int(ray_y)
            if (map_y < 0 or map_y >= self.map_height or
                map_x < 0 or map_x >= self.map_width or
                self.map_data[map_y][map_x] == "1"):
                dx = ray_x - self.player_x
                dy = ray_y - self.player_y
                return math.sqrt(dx*dx + dy*dy)

    # Update monster positions (they move toward the player).
    def update_monsters(self):
        for monster in self.monsters:
            if not monster['alive']:
                continue
            dx = self.player_x - monster['x']
            dy = self.player_y - monster['y']
            distance = math.sqrt(dx*dx + dy*dy)
            if distance < 0.5:
                # Stop game loop, notify death and ask if the player wants to restart.
                self.timer.stop()
                nuke.message("Game Over! You were killed by a monster.\nMonsters Defeated: " + str(self.monsters_defeated))
                if nuke.ask("Do you want to restart the game?"):
                    self.restart_game()
                return
            move_speed = 0.02
            monster['x'] += (dx / distance) * move_speed
            monster['y'] += (dy / distance) * move_speed

        # Spawn new monsters if there are too few alive.
        alive_monsters = [m for m in self.monsters if m['alive']]
        if len(alive_monsters) < 3:
            self.spawn_monster()

    # Randomly spawn a monster in an open area (and not too near the player).
    def spawn_monster(self, initial=False):
        attempts = 0
        while attempts < 100:
            x = random.uniform(1, self.map_width - 2)
            y = random.uniform(1, self.map_height - 2)
            if self.map_data[int(y)][int(x)] == '.':
                if math.sqrt((x - self.player_x)**2 + (y - self.player_y)**2) > 2:
                    self.monsters.append({'x': x, 'y': y, 'alive': True})
                    break
            attempts += 1

    # Restart the game by resetting the game state.
    def restart_game(self):
        self.player_x = 3.0
        self.player_y = 3.0
        self.player_angle = 0.0
        self.monsters_defeated = 0
        self.monsters = []
        self.spawn_monster(initial=True)
        self.spawn_monster(initial=True)
        self.spawn_monster(initial=True)
        self.timer.start(50)

    # Render environmental objects with higher contrast.
    def render_environment_objects(self, wall_distances):
        for obj in self.environment_objects:
            dx = obj['x'] - self.player_x
            dy = obj['y'] - self.player_y
            distance = math.sqrt(dx*dx + dy*dy)
            angle_to_obj = math.atan2(dy, dx)
            angle_diff = angle_to_obj - self.player_angle
            angle_diff = (angle_diff + math.pi) % (2 * math.pi) - math.pi
            if abs(angle_diff) < self.FOV / 2:
                screen_x = int((angle_diff + self.FOV / 2) / self.FOV * self.WIDTH)
                if screen_x < 0 or screen_x >= self.WIDTH:
                    continue
                if distance < wall_distances[screen_x]:
                    obj_height = int(self.HEIGHT / (distance + 0.0001))
                    obj_height = min(obj_height, self.HEIGHT)
                    top = (self.HEIGHT - obj_height) // 2
                    bottom = top + obj_height
                    # Render a tree as a two–column sprite with bright contrast.
                    tree_width = 2
                    for col in range(max(0, screen_x - tree_width // 2),
                                     min(self.WIDTH, screen_x - tree_width // 2 + tree_width)):
                        for row in range(top, bottom):
                            if row < top + (obj_height // 2):
                                # Bright green canopy.
                                self.grid_nodes[row][col]["tile_color"].setValue(color_to_nuke(0, 200, 0))
                            else:
                                # Vivid brown trunk.
                                self.grid_nodes[row][col]["tile_color"].setValue(color_to_nuke(120, 50, 0))

    # Render monsters with a human–like sprite (3 columns wide).
    def render_monsters(self, wall_distances):
        for monster in self.monsters:
            if not monster['alive']:
                continue
            dx = monster['x'] - self.player_x
            dy = monster['y'] - self.player_y
            distance = math.sqrt(dx*dx + dy*dy)
            angle_to_monster = math.atan2(dy, dx)
            angle_diff = angle_to_monster - self.player_angle
            angle_diff = (angle_diff + math.pi) % (2 * math.pi) - math.pi
            if abs(angle_diff) < self.FOV / 2:
                screen_x = int((angle_diff + self.FOV / 2) / self.FOV * self.WIDTH)
                if screen_x < 0 or screen_x >= self.WIDTH:
                    continue
                if distance < wall_distances[screen_x]:
                    monster_height = int(self.HEIGHT / (distance + 0.0001))
                    monster_height = min(monster_height, self.HEIGHT)
                    top = (self.HEIGHT - monster_height) // 2
                    bottom = top + monster_height
                    sprite_width = 3  # three columns for a more human-like shape
                    for col in range(max(0, screen_x - sprite_width // 2),
                                     min(self.WIDTH, screen_x - sprite_width // 2 + sprite_width)):
                        for row in range(top, bottom):
                            rel = (row - top) / float(monster_height)
                            if rel < 0.2:
                                # Head: center is flesh-colored, sides black for outline.
                                if col == screen_x:
                                    color = (255, 220, 177)
                                else:
                                    color = (0, 0, 0)
                            elif rel < 0.7:
                                # Torso: red with alternating black details.
                                if (col - (screen_x - sprite_width // 2)) % 2 == 0:
                                    color = (180, 0, 0)
                                else:
                                    color = (0, 0, 0)
                            else:
                                # Legs: dark with slight variation.
                                if (col - (screen_x - sprite_width // 2)) % 2 == 0:
                                    color = (50, 0, 0)
                                else:
                                    color = (0, 0, 0)
                            self.grid_nodes[row][col]["tile_color"].setValue(color_to_nuke(*color))

    # Render the whole frame.
    def render(self):
        wall_distances = [0] * self.WIDTH
        for col in range(self.WIDTH):
            ray_angle = self.player_angle - self.FOV / 2 + (col / float(self.WIDTH)) * self.FOV
            distance = self.cast_ray(ray_angle)
            wall_distances[col] = distance
            wall_height = int(self.HEIGHT / (distance + 0.0001))
            wall_height = min(wall_height, self.HEIGHT)
            wall_start = (self.HEIGHT - wall_height) // 2
            wall_end = wall_start + wall_height
            for row in range(self.HEIGHT):
                # Dark, high-contrast colors for the background:
                if row < wall_start:
                    # Ceiling (sky): very dark blue.
                    self.grid_nodes[row][col]["tile_color"].setValue(color_to_nuke(0, 0, 10))
                elif wall_start <= row < wall_end:
                    # Wall: dark gray.
                    self.grid_nodes[row][col]["tile_color"].setValue(color_to_nuke(40, 40, 40))
                else:
                    # Floor (ground): very dark brown.
                    self.grid_nodes[row][col]["tile_color"].setValue(color_to_nuke(10, 5, 0))
        self.render_environment_objects(wall_distances)
        self.render_monsters(wall_distances)
        
        # Draw the player pointer (crosshair) at the center using the current pointer color.
        pointer_col = self.WIDTH // 2
        pointer_row = self.HEIGHT // 2
        pointer_coords = [
            (pointer_row, pointer_col),
            (pointer_row - 1, pointer_col),
            (pointer_row + 1, pointer_col),
            (pointer_row, pointer_col - 1),
            (pointer_row, pointer_col + 1)
        ]
        for r, c in pointer_coords:
            if 0 <= r < self.HEIGHT and 0 <= c < self.WIDTH:
                self.grid_nodes[r][c]["tile_color"].setValue(color_to_nuke(*self.pointer_color))
                
        # Update the backdrop counter with the number of monsters defeated.
        self.backdrop["label"].setValue("Monsters Defeated: " + str(self.monsters_defeated))

    # Main game loop: update monsters then render the scene.
    def game_loop(self):
        self.update_monsters()
        self.render()

    # Movement and control methods.
    def move_forward(self):
        step = 0.5
        self.player_x += math.cos(self.player_angle) * step
        self.player_y += math.sin(self.player_angle) * step

    def move_backward(self):
        step = 0.5
        self.player_x -= math.cos(self.player_angle) * step
        self.player_y -= math.sin(self.player_angle) * step

    def rotate_left(self):
        self.player_angle -= 0.1

    def rotate_right(self):
        self.player_angle += 0.1

    # Shooting: if a monster is nearly centered and within range, mark it as dead.
    # Also, change the pointer color to red temporarily.
    def shoot(self):
        hit = False
        for monster in self.monsters:
            if not monster['alive']:
                continue
            dx = monster['x'] - self.player_x
            dy = monster['y'] - self.player_y
            distance = math.sqrt(dx*dx + dy*dy)
            angle_to_monster = math.atan2(dy, dx)
            angle_diff = angle_to_monster - self.player_angle
            angle_diff = (angle_diff + math.pi) % (2 * math.pi) - math.pi
            if abs(angle_diff) < 0.1 and distance < 5.0:
                monster['alive'] = False
                hit = True
                self.monsters_defeated += 1
        if not hit:
            self.monsters_defeated = max(0, self.monsters_defeated - 1)
        
        # Change the pointer color to red for a short time to indicate shooting.
        self.pointer_color = (255, 0, 0)
        QTimer.singleShot(100, lambda: setattr(self, 'pointer_color', (255, 255, 255)))

# A key listener that installs an event filter on the QApplication instance.
class PlayerKeyListener(QObject):
    def __init__(self, game):
        super(PlayerKeyListener, self).__init__()
        self.game = game
        self.app = QApplication.instance()
        if not self.app:
            self.app = QApplication([])
        self.app.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        if isinstance(event, QKeyEvent) and event.type() == QKeyEvent.KeyPress:
            key = event.key()
            if key == Qt.Key_Up:
                self.game.move_forward()
                return True
            elif key == Qt.Key_Down:
                self.game.move_backward()
                return True
            elif key == Qt.Key_Left:
                self.game.rotate_left()
                return True
            elif key == Qt.Key_Right:
                self.game.rotate_right()
                return True
            elif key == Qt.Key_Space:
                self.game.shoot()
                return True
        return False

# Instantiate the game and set up the key listener.
game = Game()
key_listener = PlayerKeyListener(game)
