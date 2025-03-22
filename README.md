# Nuke Games: A Fun Break for VFX Compositors

Welcome to **Nuke Games**! 🎮 This repository is your ultimate escape from the intense world of VFX compositing. Take a break and enjoy some classic arcade games right inside Nuke. We've got three exciting games for you: **Arkanoid**, **Monster**, and **Nuke Tower**.

## Games Included

### Arkanoid
Break all the blocks with your ball and paddle. Move the paddle left and right to keep the ball in play and destroy all the blocks to win!

### Monster
Catch the good dots and avoid the bad ones! Move your plate to collect the falling dots. White dots are good, red dots are bad. Miss a good dot or catch a bad one, and it's game over!

### Nuke Tower
Jump from platform to platform and climb as high as you can! Avoid falling off the screen and keep an eye on your score. The higher you go, the faster the platforms fall!

## How to Install

1. **Clone the repository**:
    ```sh
    git clone https://github.com/aramadan0096/nuke-games.git
    ```

2. **Move the contents** of the `GIZMOS` folder to your `/user/.nuke` directory.

3. **Edit your `init.py`** file in `/user/.nuke` to include the following lines:
    ```python
    nuke.pluginAddPath(r"./NukeGames")
    ```

4. **Start Nuke** and enjoy the games from the custom "AR" menu!

## How to Play

### Arkanoid
- **Start the game**: `Ctrl+Alt+B`
- **Move Left**: Left Arrow Key
- **Move Right**: Right Arrow Key

### Monster
- **Start the game**: `Ctrl+Alt+M`
- **Move Left**: Left Arrow Key
- **Move Right**: Right Arrow Key

### Nuke Tower
- **Start the game**: `Ctrl+Alt+T`
- **Move Left**: Left Arrow Key
- **Move Right**: Right Arrow Key
- **Jump**: Space Bar

## Background Images

- **horizontalBG.jpg** and **verticalBG.jpg** are used as the backdrop for the games.
- **Copyright**: [rawpixel](https://www.freepik.com/author/rawpixel-com).

## Exclamation
- Since the Nuke node graph is not designed for this kind of game, please keep it away from your Comping.

Enjoy your break and happy Comping! 🎉
