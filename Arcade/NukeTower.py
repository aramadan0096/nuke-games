import nuke
import random
from PySide2.QtCore import QTimer, QObject, Qt
from PySide2.QtWidgets import QApplication, QMessageBox
from PySide2.QtGui import QKeyEvent

# Physics and game constants
GRAVITY = 1.0          # Gravitational acceleration
JUMP_VELOCITY = -20    # Jump impulse (negative because y increases downward)
MOVE_STEP = 20         # Horizontal movement increment

# Dimensions for game objects
PLAYER_WIDTH = 50
PLAYER_HEIGHT = 50
PLATFORM_WIDTH = 100
PLATFORM_HEIGHT = 10

# Backdrop dimensions and position
BACKDROP_X = 50
BACKDROP_Y = 50
BACKDROP_WIDTH = 400
BACKDROP_HEIGHT = 800

# Vertical spacing between platforms
PLATFORM_SPACING = 150

class IcyTowerGame(QObject):
    def __init__(self):
        super(IcyTowerGame, self).__init__()
        self.score = 0
        self.player_on_platform = False
        # Count the number of platform landings during safe mode
        self.platforms_jumped = 0  
        # Define a safe line (the bottom where the player starts)
        self.safe_line = BACKDROP_Y + BACKDROP_HEIGHT - PLAYER_HEIGHT
        self.setup_game()
        self.generate_initial_platforms()
        self.game_timer = QTimer()
        self.game_timer.timeout.connect(self.update_game)
        self.game_timer.start(50)

    def setup_game(self):
        """Sets up the game scene: the backdrop, the player and initial nodes."""
        # Create a backdrop node which will contain all platforms
        self.backdrop = nuke.nodes.BackdropNode(
            bdwidth=BACKDROP_WIDTH,
            bdheight=BACKDROP_HEIGHT,
            xpos=BACKDROP_X,
            ypos=BACKDROP_Y,
            label=f'<h1>Score: {self.score}</h1>'
        )
        # Create the player as an Axis node
        self.player = nuke.nodes.Axis(name="Player")
        # Place player at the bottom center of the backdrop
        self.player['xpos'].setValue(BACKDROP_X + (BACKDROP_WIDTH - PLAYER_WIDTH) / 2)
        self.player['ypos'].setValue(self.safe_line)
        self.platforms = []

    def generate_initial_platforms(self):
        """Generate a series of platforms from the bottom of the backdrop upward."""
        # Ensure a platform directly at the bottom so the player can start on it
        self.create_platform(BACKDROP_Y + BACKDROP_HEIGHT)
        y = BACKDROP_Y + BACKDROP_HEIGHT - PLATFORM_SPACING
        while y > BACKDROP_Y:
            self.create_platform(y)
            y -= PLATFORM_SPACING

    def create_platform(self, y):
        """Creates a platform (a NoOp node) at a given y coordinate with random x position."""
        x_min = BACKDROP_X
        x_max = BACKDROP_X + BACKDROP_WIDTH - PLATFORM_WIDTH
        x = random.randint(int(x_min), int(x_max))
        platform = nuke.nodes.NoOp(name="Platform", hide_input=True)
        platform['xpos'].setValue(x)
        platform['ypos'].setValue(y)
        self.platforms.append(platform)
        return platform

    def update_game(self):
        """Main game loop: update physics, check for collisions and manage upward scrolling."""
        # Apply gravity to the player's vertical velocity
        self.player_velocity_y = getattr(self, 'player_velocity_y', 0) + GRAVITY

        # Update the player's vertical position
        current_y = self.player['ypos'].value()
        new_y = current_y + self.player_velocity_y
        self.player['ypos'].setValue(new_y)

        # If falling, check for landing on a platform
        if self.player_velocity_y > 0:
            for platform in self.platforms:
                plat_x = platform['xpos'].value()
                plat_y = platform['ypos'].value()
                player_x = self.player['xpos'].value() + PLAYER_WIDTH / 2  # Use center of the player
                # Check horizontal overlap and vertical collision (landing from above)
                if (player_x >= plat_x and player_x <= plat_x + PLATFORM_WIDTH):
                    if current_y + PLAYER_HEIGHT <= plat_y and new_y + PLAYER_HEIGHT >= plat_y:
                        # Snap the player on top of the platform and reset vertical velocity
                        self.player['ypos'].setValue(plat_y - PLAYER_HEIGHT)
                        self.player_velocity_y = 0
                        # If landing for the first time, count it and disable safe mode eventually
                        if not self.player_on_platform:
                            self.platforms_jumped += 1
                        self.player_on_platform = True
                        # Update score based on the platform's height (the higher, the better)
                        self.score = max(self.score, int((BACKDROP_Y + BACKDROP_HEIGHT) - plat_y))
                        self.backdrop['label'].setValue(f'<h1>Score: {self.score}</h1>')
                        break
                    else:
                        self.player_on_platform = False

        # In safe mode (first three platform landings), prevent falling off the bottom.
        if self.platforms_jumped < 3:
            if new_y > self.safe_line:
                self.player['ypos'].setValue(self.safe_line)
                self.player_velocity_y = 0
        else:
            # Check for game over: if the player falls below the backdrop
            if new_y > BACKDROP_Y + BACKDROP_HEIGHT:
                self.end_game("Game Over! You fell off the tower.")

        # If the player climbs above a threshold, shift the scene downward
        threshold = BACKDROP_Y + BACKDROP_HEIGHT / 3
        if new_y < threshold:
            delta = threshold - new_y
            # Keep player at the threshold while moving the platforms
            self.player['ypos'].setValue(threshold)
            for platform in self.platforms:
                plat_y = platform['ypos'].value()
                platform['ypos'].setValue(plat_y + delta)
            # Increase score based on the distance climbed
            self.score += int(delta)
            self.backdrop['label'].setValue(f'<h1>Score: {self.score}</h1>')
            # Add new platforms at the top if needed
            highest_platform_y = min([p['ypos'].value() for p in self.platforms]) if self.platforms else BACKDROP_Y
            while highest_platform_y > BACKDROP_Y:
                new_platform = self.create_platform(highest_platform_y - PLATFORM_SPACING)
                highest_platform_y = new_platform['ypos'].value()

    def player_jump(self):
        """Make the player jump if they are standing on a platform or on the ground."""
        if self.player_on_platform or self.player['ypos'].value() >= self.safe_line:
            self.player_velocity_y = JUMP_VELOCITY
            self.player_on_platform = False

    def end_game(self, message):
        """Stop the game and display a game over message."""
        self.game_timer.stop()
        QMessageBox.critical(None, "Game Over", message)


class PlayerKeyListener(QObject):
    def __init__(self, game):
        super(PlayerKeyListener, self).__init__()
        self.game = game
        self.app = QApplication.instance()
        if not self.app:
            self.app = QApplication([])
        self.app.installEventFilter(self)
        self.move_step = MOVE_STEP

    def eventFilter(self, obj, event):
        if isinstance(event, QKeyEvent) and event.type() == QKeyEvent.KeyPress:
            key = event.key()
            if key == Qt.Key_Left:
                self.move_player(-self.move_step)
                return True
            elif key == Qt.Key_Right:
                self.move_player(self.move_step)
                return True
            elif key == Qt.Key_Space:
                self.game.player_jump()
                return True
        return False

    def move_player(self, delta):
        """Move the player horizontally while keeping them within the backdrop bounds."""
        current_x = self.game.player['xpos'].value()
        new_x = current_x + delta
        left_bound = BACKDROP_X
        right_bound = BACKDROP_X + BACKDROP_WIDTH - PLAYER_WIDTH
        if new_x < left_bound:
            new_x = left_bound
        elif new_x > right_bound:
            new_x = right_bound
        self.game.player['xpos'].setValue(new_x)


def start_icy_tower_game():
    global game, key_listener
    game = IcyTowerGame()
    key_listener = PlayerKeyListener(game)
    # Optionally, set the Nuke viewer or zoom as needed
    # nuke.zoom(1, [BACKDROP_X + BACKDROP_WIDTH/2, BACKDROP_Y + BACKDROP_HEIGHT/2])

# Uncomment the line below to run the game when the script is executed.
start_icy_tower_game()
