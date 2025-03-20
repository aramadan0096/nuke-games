import nuke
from PySide2.QtCore import QTimer, Qt, QObject
from PySide2.QtWidgets import QApplication
from PySide2.QtGui import QKeyEvent

# Define dimensions for collision detection
PLAYER_WIDTH = 100
PLAYER_HEIGHT = 20

class NukeGame2(QObject):
    def __init__(self):
        super(NukeGame2, self).__init__()
        self.collected_count = 0
        self.setup_game()
        # Set monster movement: horizontal movement only.
        self.monster_dx = 7   # horizontal speed
        # No vertical movement for the monster.
        self.monster_dy = 0
        # Set dot falling speed
        self.dot_dy = 5
        # Timer to update monster and dot positions
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_game)
        self.timer.start(50)
        # Timer for the monster to drop dots periodically
        self.dot_timer = QTimer()
        self.dot_timer.timeout.connect(self.drop_dot)
        self.dot_timer.start(1000)  # drop a dot every 1 second

    def setup_game(self):
        # Create a vertical backdrop: width=400, height=800.
        # Its label shows the collected dot count.
        self.backdrop = nuke.nodes.BackdropNode(
            bdwidth=400,
            bdheight=800,
            xpos=50,
            ypos=50,
            label="Collected: 0"
        )
        # Create the player plate (a NoOp node) positioned near the bottom.
        self.player_plate = nuke.nodes.NoOp(name="player plate")
        self.player_plate['xpos'].setValue(150)  # horizontal position
        self.player_plate['ypos'].setValue(750)   # near the bottom (backdrop y=50+height=800 gives bottom=850)
        
        # Create the monster (a NoOp node) that bounces horizontally within the backdrop.
        self.monster = nuke.nodes.NoOp(name="monster")
        self.monster['xpos'].setValue(175)
        self.monster['ypos'].setValue(100)  # Fixed vertical position

        # List to hold active Dot nodes dropped by the monster.
        self.dots = []

    def update_game(self):
        # --- Update Monster Position (only horizontal) ---
        monster_x = self.monster['xpos'].value()
        new_monster_x = monster_x + self.monster_dx
        # Keep the Y position constant.
        new_monster_y = self.monster['ypos'].value()

        # Get backdrop boundaries.
        bd_x = self.backdrop['xpos'].value()
        bd_y = self.backdrop['ypos'].value()
        bd_width = self.backdrop['bdwidth'].value()
        bd_height = self.backdrop['bdheight'].value()
        left_edge = bd_x
        right_edge = bd_x + bd_width

        # Bounce off left/right boundaries for the monster.
        if new_monster_x <= left_edge:
            new_monster_x = left_edge
            self.monster_dx = abs(self.monster_dx)
        elif new_monster_x >= right_edge:
            new_monster_x = right_edge
            self.monster_dx = -abs(self.monster_dx)
        self.monster['xpos'].setValue(new_monster_x)
        self.monster['ypos'].setValue(new_monster_y)

        # --- Update Dot Nodes ---
        dots_to_remove = []
        for dot in self.dots:
            dot_x = dot['xpos'].value()
            dot_y = dot['ypos'].value() + self.dot_dy
            dot['ypos'].setValue(dot_y)
            
            # Check collision with the player plate.
            plate_x = self.player_plate['xpos'].value()
            plate_y = self.player_plate['ypos'].value()
            if (dot_x >= plate_x and dot_x <= plate_x + PLAYER_WIDTH and
                dot_y >= plate_y and dot_y <= plate_y + PLAYER_HEIGHT):
                # Dot collected: update counter and backdrop label.
                self.collected_count += 1
                dots_to_remove.append(dot)
                self.backdrop['label'].setValue(f"Collected: {self.collected_count}")
            
            # If a dot reaches the bottom of the backdrop, end the game.
            bd_bottom = bd_y + bd_height
            if dot_y >= bd_bottom:
                nuke.message("Game Over")
                self.timer.stop()
                self.dot_timer.stop()
                return

        # Remove collected dots.
        for dot in dots_to_remove:
            if dot in self.dots:
                self.dots.remove(dot)
                nuke.delete(dot)

    def drop_dot(self):
        # Monster drops a dot at its current position.
        dot = nuke.nodes.Dot(name="dot")
        dot['xpos'].setValue(self.monster['xpos'].value())
        dot['ypos'].setValue(self.monster['ypos'].value())
        self.dots.append(dot)


class PlayerKeyListener(QObject):
    def __init__(self, game):
        super(PlayerKeyListener, self).__init__()
        self.game = game
        self.app = QApplication.instance()
        if not self.app:
            self.app = QApplication([])
        self.app.installEventFilter(self)
        self.move_step = 20  # pixels to move per key press

    def eventFilter(self, obj, event):
        if isinstance(event, QKeyEvent):
            if event.type() == QKeyEvent.KeyPress:
                # Move left with Left arrow key.
                if event.key() == Qt.Key_Left:
                    self.move_player(-self.move_step)
                    return True
                # Move right with Right arrow key.
                elif event.key() == Qt.Key_Right:
                    self.move_player(self.move_step)
                    return True
        return False

    def move_player(self, delta):
        current_x = self.game.player_plate['xpos'].value()
        new_x = current_x + delta
        self.game.player_plate['xpos'].setValue(new_x)
        print("Player moved to", new_x)


def start_nuke_game():
    global game, key_listener
    game = NukeGame2()
    key_listener = PlayerKeyListener(game)
