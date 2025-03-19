import nuke
import monster
import blocks

# Create a custom menu named "AR"
menu = nuke.menu('Nuke')
ar_menu = menu.addMenu('AR')

# Add menu items to the "AR" menu
# ar_menu.addCommand('Blocks', blocks.blocks_launcher())
ar_menu.addCommand('Monster', monster)