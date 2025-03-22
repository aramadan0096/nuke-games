import nuke
import webbrowser

import blocks
import monster
import NukeTower

def open_about_page():
    webbrowser.open('https://www.linkedin.com/in/a-ramadan0096')
    
# Create a custom menu named "AR"
menu = nuke.menu('Nuke')
ar_menu = menu.addMenu('AR')

# Add menu items to the "AR" menu
ar_menu.addCommand('Games/Arkanoid', 'blocks.start_nuke_game()', 'Ctrl+Alt+B')
ar_menu.addCommand('Games/Monster', 'monster.start_nuke_game()', 'Ctrl+Alt+M')
ar_menu.addCommand('Games/Nuke Tower', 'NukeTower.start_icy_tower_game()', 'Ctrl+Alt+T')

# Add a separator
ar_menu.addSeparator()

# Add an "About" menu item
ar_menu.addCommand('Credits', 'open_about_page()')