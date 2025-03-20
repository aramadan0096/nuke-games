import nuke
import random
from PySide2.QtCore import QTimer, Qt, QObject
from PySide2.QtWidgets import QApplication, QMessageBox
from PySide2.QtGui import QKeyEvent

# Define constants
PLAYER_WIDTH = 100
PLAYER_HEIGHT = 20

good_dot_color = 4294967295  # White
bad_dot_color = 255  # black
class NukeGame2(QObject):
    def __init__(self):
        super(NukeGame2, self).__init__()
        self.collected_count = 0
        self.setup_game()
        self.monster_dx = 7  # Monster movement speed
        self.dot_dy = 5       # Dot falling speed
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_game)
        self.timer.start(50)
        self.schedule_next_drop()  # Schedule first dot drop

    def setup_game(self):
        """Creates the game environment."""
        self.backdrop = nuke.nodes.BackdropNode(
            bdwidth=400,
            bdheight=800,
            xpos=50,
            ypos=50,
            label="Collected: 0"
        )

        self.player_plate = nuke.nodes.NoOp(name="player plate")
        self.player_plate['xpos'].setValue(150)
        self.player_plate['ypos'].setValue(750)

        self.monster = nuke.nodes.NoOp(name="monster")
        self.monster['xpos'].setValue(175)
        self.monster['ypos'].setValue(100)

        self.dots = []

    def update_game(self):
        """Moves the monster and updates dot positions."""
        monster_x = self.monster['xpos'].value()
        new_monster_x = monster_x + self.monster_dx
        bd_x = self.backdrop['xpos'].value()
        bd_width = self.backdrop['bdwidth'].value()
        left_edge = bd_x
        right_edge = bd_x + bd_width

        # Bounce monster off edges
        if new_monster_x <= left_edge:
            new_monster_x = left_edge
            self.monster_dx = abs(self.monster_dx)
        elif new_monster_x >= right_edge:
            new_monster_x = right_edge
            self.monster_dx = -abs(self.monster_dx)
        self.monster['xpos'].setValue(new_monster_x)

        # Update dots
        dots_to_remove = []
        for dot in self.dots:
            dot_x = dot['xpos'].value()
            dot_y = dot['ypos'].value() + self.dot_dy
            dot['ypos'].setValue(dot_y)

            # Get dot color
            dot_color = dot['tile_color'].value()

            # Collision with player
            plate_x = self.player_plate['xpos'].value()
            plate_y = self.player_plate['ypos'].value()
            if (dot_x >= plate_x and dot_x <= plate_x + PLAYER_WIDTH and
                dot_y >= plate_y and dot_y <= plate_y + PLAYER_HEIGHT):
                
                if dot_color == good_dot_color:  # White Dot (Good)
                    self.collected_count += 1
                    self.backdrop['label'].setValue(f"Collected: {self.collected_count}")
                elif dot_color == bad_dot_color:  # Red Dot (Bad)
                    self.end_game("You hit a bad dot!")

                dots_to_remove.append(dot)

            # If white dot reaches the bottom, game over
            bd_bottom = self.backdrop['ypos'].value() + self.backdrop['bdheight'].value()
            if dot_y >= bd_bottom:
                if dot_color == good_dot_color:  # Good dot not collected
                    self.end_game("You missed a good dot!")
                else:
                    dots_to_remove.append(dot)  # Red dots disappear normally

        # Remove collected and fallen dots
        for dot in dots_to_remove:
            if dot in self.dots:
                self.dots.remove(dot)
                nuke.delete(dot)

    def schedule_next_drop(self):
        """Schedules the next dot drop at a random time interval."""
        drop_interval = random.randint(500, 1500)  # Random between 0.5s - 1.5s
        self.dot_timer = QTimer()
        self.dot_timer.singleShot(drop_interval, self.drop_dot)

    def drop_dot(self):
        """Drops a dot with an 80% chance of being white and 20% chance of being red."""
        dot = nuke.nodes.Dot(name="dot")
        dot['xpos'].setValue(self.monster['xpos'].value())
        dot['ypos'].setValue(self.monster['ypos'].value())

        # 80% chance for white, 20% for red
        is_white_dot = random.choices([True, False], weights=[80, 20])[0]
        dot['tile_color'].setValue(good_dot_color if is_white_dot else bad_dot_color)  # White or Red

        self.dots.append(dot)
        self.schedule_next_drop()  # Schedule next drop

    def end_game(self, message):
        """Ends the game with a message."""
        self.timer.stop()
        self.dot_timer.stop()
        QMessageBox.critical(None, "Game Over", message)
        for dot in self.dots:
            nuke.delete(dot)
        self.dots.clear()


class PlayerKeyListener(QObject):
    def __init__(self, game):
        super(PlayerKeyListener, self).__init__()
        self.game = game
        self.app = QApplication.instance()
        if not self.app:
            self.app = QApplication([])
        self.app.installEventFilter(self)
        self.move_step = 20

    def eventFilter(self, obj, event):
        if isinstance(event, QKeyEvent) and event.type() == QKeyEvent.KeyPress:
            if event.key() == Qt.Key_Left:
                self.move_player(-self.move_step)
                return True
            elif event.key() == Qt.Key_Right:
                self.move_player(self.move_step)
                return True
        return False

    def move_player(self, delta):
        current_x = self.game.player_plate['xpos'].value()
        new_x = current_x + delta
        self.game.player_plate['xpos'].setValue(new_x)


def start_nuke_game():
    global game, key_listener
    game = NukeGame2()
    key_listener = PlayerKeyListener(game)
