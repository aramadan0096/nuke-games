import nuke
import random
from PySide2.QtCore import QTimer, Qt, QObject
from PySide2.QtWidgets import QApplication
from PySide2.QtGui import QKeyEvent

# Define dimensions for collision detection
PLAYER_WIDTH = 100
PLAYER_HEIGHT = 20
BLOCK_WIDTH = 80
BLOCK_HEIGHT = 40

class NukeGame(QObject):
    def __init__(self):
        super(NukeGame, self).__init__()
        self.setup_game()
        # Set initial ball movement (dx, dy)
        self.ball_dx = 5    # horizontal speed
        self.ball_dy = -5   # vertical speed (-ve means upward)
        # Timer to update ball position periodically (every 50 ms)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ball)
        self.timer.start(50)

    def setup_game(self):
        # Create a backdrop node to define the game area.
        # The backdrop's top-left corner is at (50, 50) and its size is 800 x 380.
        self.backdrop = nuke.nodes.BackdropNode(
            bdwidth=800,
            bdheight=380,
            xpos=50,
            ypos=50,
            label=r'<img src="horizontalBG.jpg" width="795">'
        )

        nuke.zoom(1, [400, 300])
        
        # Create the player plate (a NoOp node) positioned near the bottom.
        self.player_plate = nuke.nodes.NoOp(name="player plate", hide_input=True)
        self.player_plate['xpos'].setValue(200)
        self.player_plate['ypos'].setValue(350)  # Placed inside the 400 height area

        # Create blocks: 3 rows x 8 columns
        self.blocks = []
        block_start_x = 100
        block_start_y = 100
        for row in range(3):
            for col in range(8):
                block = nuke.nodes.NoOp(name=f"block_{row}_{col}", hide_input = True)
                xpos = block_start_x + col * (BLOCK_WIDTH + 10)
                ypos = block_start_y + row * (BLOCK_HEIGHT + 10)
                block['xpos'].setValue(xpos)
                block['ypos'].setValue(ypos)
                # Set a random tile color (using a random integer value)
                random_color = random.randint(0, 0xFFFFFF)
                block['tile_color'].setValue(random_color)
                self.blocks.append(block)

        # Create the ball as a Dot node
        self.ball = nuke.nodes.Dot(name="ball", hide_input=True)
        self.ball['xpos'].setValue(250)
        self.ball['ypos'].setValue(330)  # Starting just above the player plate

    def update_ball(self):
        current_x = self.ball['xpos'].value()
        current_y = self.ball['ypos'].value()
        new_x = current_x + self.ball_dx
        new_y = current_y + self.ball_dy

        # Get backdrop boundaries
        bd_x = self.backdrop['xpos'].value()
        bd_y = self.backdrop['ypos'].value()
        bd_width = self.backdrop['bdwidth'].value()
        bd_height = self.backdrop['bdheight'].value()
        left_edge = bd_x
        right_edge = bd_x + bd_width
        top_edge = bd_y
        bottom_edge = bd_y + bd_height

        # --- Check backdrop boundaries ---
        # Left edge
        if new_x <= left_edge:
            new_x = left_edge
            self.ball_dx = abs(self.ball_dx)  # bounce right

        # Right edge
        elif new_x >= right_edge:
            new_x = right_edge
            self.ball_dx = -abs(self.ball_dx)  # bounce left

        # Top edge
        if new_y <= top_edge:
            new_y = top_edge
            self.ball_dy = abs(self.ball_dy)  # bounce downward

        # Bottom edge: game over
        if new_y >= bottom_edge:
            nuke.message("Game Over")
            self.timer.stop()
            return  # Exit without updating the ball position

        # --- Collision with player plate ---
        plate_x = self.player_plate['xpos'].value()
        plate_y = self.player_plate['ypos'].value()
        if (new_x >= plate_x and new_x <= plate_x + PLAYER_WIDTH and
            new_y >= plate_y and new_y <= plate_y + PLAYER_HEIGHT):
            # Bounce the ball upward
            self.ball_dy = -abs(self.ball_dy)
            new_y = plate_y - 1  # Adjust the ball to just above the plate

        # --- Collision with blocks ---
        blocks_to_remove = []
        for block in self.blocks:
            block_x = block['xpos'].value()
            block_y = block['ypos'].value()
            if (new_x >= block_x and new_x <= block_x + BLOCK_WIDTH and
                new_y >= block_y and new_y <= block_y + BLOCK_HEIGHT):
                # Bounce the ball downward
                self.ball_dy = abs(self.ball_dy)
                blocks_to_remove.append(block)

        # Remove any hit blocks from the scene
        for block in blocks_to_remove:
            self.blocks.remove(block)
            nuke.delete(block)
            # print("Block hit and removed:", block.name())

        # Check if all blocks have been removed: win condition!
        if not self.blocks:
            nuke.message("Congratulations")
            self.timer.stop()
            return

        # Update ball position
        self.ball['xpos'].setValue(new_x)
        self.ball['ypos'].setValue(new_y)


class PlayerKeyListener(QObject):
    def __init__(self, game):
        super(PlayerKeyListener, self).__init__()
        self.game = game
        self.app = QApplication.instance()
        if not self.app:
            self.app = QApplication([])
        # Install event filter to capture key presses
        self.app.installEventFilter(self)
        self.move_step = 20  # How many pixels to move the player plate per key press

    def eventFilter(self, obj, event):
        if isinstance(event, QKeyEvent):
            if event.type() == QKeyEvent.KeyPress:
                # Move left with Left arrow key
                if event.key() == Qt.Key_Left:
                    self.move_player(-self.move_step)
                    return True
                # Move right with Right arrow key
                elif event.key() == Qt.Key_Right:
                    self.move_player(self.move_step)
                    return True
        return False

    def move_player(self, delta):
        current_x = self.game.player_plate['xpos'].value()
        new_x = current_x + delta
        self.game.player_plate['xpos'].setValue(new_x)
        # print("Player moved to", new_x)

def start_nuke_game():
    global game, key_listener
    # Initialize the game and the key listener
    game = NukeGame()
    key_listener = PlayerKeyListener(game)
