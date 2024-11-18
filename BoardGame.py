from flask import Flask, render_template, request, redirect, url_for, session
import random
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change to a secure key

# Game settings
BOARD_SPACES = 30
BONUSES = {5: 2, 12: 3, 20: 4}  # Bonus spaces (space: additional moves)
SETBACKS = {8: -3, 15: -2, 25: -4}  # Setback spaces (space: move back)

# Initial game state
DEFAULT_STATE = {
    'players': {
        'Player1': {'name': 'Player 1', 'position': 1, 'score': 0},
        'Player2': {'name': 'Player 2', 'position': 1, 'score': 0}
    },
    'current_turn': 'Player1',
    'winner': None
}

@app.route('/')
def index():
    if 'game_state' not in session:
        session['game_state'] = DEFAULT_STATE.copy()
    return render_template('index.html', game=session['game_state'], board_spaces=BOARD_SPACES, bonuses=BONUSES, setbacks=SETBACKS)

@app.route('/roll_dice')
def roll_dice():
    game = session['game_state']
    current_player = game['current_turn']
    dice_roll = random.randint(1, 6)
    game['players'][current_player]['position'] += dice_roll

    # Check board events
    pos = game['players'][current_player]['position']
    if pos in BONUSES:
        game['players'][current_player]['position'] += BONUSES[pos]
    elif pos in SETBACKS:
        game['players'][current_player]['position'] += SETBACKS[pos]

    # Keep the position within bounds
    game['players'][current_player]['position'] = min(max(game['players'][current_player]['position'], 1), BOARD_SPACES)

    # Check for a winner
    if game['players'][current_player]['position'] >= BOARD_SPACES:
        game['winner'] = current_player
    else:
        # Switch turn
        game['current_turn'] = 'Player2' if current_player == 'Player1' else 'Player1'

    session['game_state'] = game
    return redirect(url_for('index'))

@app.route('/save_game')
def save_game():
    game = session['game_state']
    with open('game_save.txt', 'w') as f:
        f.write(str(game))
    return redirect(url_for('index'))

@app.route('/load_game')
def load_game():
    if os.path.exists('game_save.txt'):
        with open('game_save.txt', 'r') as f:
            session['game_state'] = eval(f.read())
    return redirect(url_for('index'))

@app.route('/reset_game')
def reset_game():
    session['game_state'] = DEFAULT_STATE.copy()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True) 