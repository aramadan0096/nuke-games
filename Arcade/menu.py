import nuke

import blocks
import monster
import NukeTower

# Create a custom menu named "AR"
menu = nuke.menu('Nuke')
ar_menu = menu.addMenu('AR')

# Add menu items to the "AR" menu
ar_menu.addCommand('Games/Arkanoid', 'blocks.start_nuke_game()', 'Ctrl+Alt+B')
ar_menu.addCommand('Games/Monster', 'monster.start_nuke_game()', 'Ctrl+Alt+M')
ar_menu.addCommand('Games/Nuke Tower', 'NukeTower.start_icy_tower_game()', 'Ctrl+Alt+T')