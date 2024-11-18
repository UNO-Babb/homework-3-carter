from flask import Flask, render_template, request, jsonify
import random
import json
import os

app = Flask(__name__)

GAME_STATE_FILE = 'game_state.json'

# Initialize game state
def initialize_game_state():
    return {
        "players": {
            "Red": {"position": 1, "turns_lost": 0},
            "Blue": {"position": 1, "turns_lost": 0}
        },
        "current_turn": "Red",
        "event_log": ["Game started!"],
        "winner": None
    }

def load_game_state():
    if os.path.exists(GAME_STATE_FILE):
        with open(GAME_STATE_FILE, 'r') as f:
            state = json.load(f)
        if 'winner' not in state:
            state['winner'] = None
        return state
    return initialize_game_state()

def save_game_state(state):
    with open(GAME_STATE_FILE, 'w') as f:
        json.dump(state, f)

@app.route('/')
def index():
    game_state = load_game_state()
    return render_template('index.html', game_state=game_state)

@app.route('/roll_dice', methods=['POST'])
def roll_dice():
    game_state = load_game_state()
    if game_state["winner"]:
        return jsonify({"message": "game_over", "winner": game_state["winner"], "event_log": game_state["event_log"]})

    dice_value = random.randint(1, 6)
    current_player = game_state["current_turn"]
    opponent = "Blue" if current_player == "Red" else "Red"
    player_data = game_state["players"][current_player]

    if player_data["turns_lost"] > 0:
        player_data["turns_lost"] -= 1
        game_state["event_log"].append(f"{current_player} loses a turn.")
    else:
        new_position = player_data["position"] + dice_value

        if new_position > 38:
            game_state["winner"] = current_player
            game_state["event_log"].append(f"{current_player} wins the game!")
            save_game_state(game_state)
            return jsonify({"message": "win", "winner": current_player, "event_log": game_state["event_log"]})

        player_data["position"] = new_position
        game_state["event_log"].append(f"{current_player} rolled {dice_value} and moved to space {new_position}.")

        if new_position in [7, 14, 25, 33]:
            handle_bonus(game_state, current_player, opponent, new_position)
        elif new_position in [9, 17, 27, 38]:
            handle_setback(game_state, current_player, new_position)

        if game_state["players"][opponent]["position"] == new_position:
            game_state["event_log"].append(f"Crash! Both players roll back.")
            crash(game_state, current_player, opponent)

    if "Roll again" not in game_state["event_log"][-1]:
        game_state["current_turn"] = opponent

    save_game_state(game_state)
    return jsonify({"dice_value": dice_value, "event_log": game_state["event_log"]})

@app.route('/reset_game', methods=['POST'])
def reset_game():
    save_game_state(initialize_game_state())
    return jsonify({"message": "reset"})

def handle_bonus(game_state, player, opponent, position):
    bonuses = {
        7: "Boost! Move forward 1 space.",
        14: "Pit Maneuver! Opponent loses a turn.",
        25: "Slipstream! Move forward 2 spaces if opponent is ahead.",
        33: "Pit Crew Advice! Roll again."
    }
    game_state["event_log"].append(f"{player} landed on a bonus space: {bonuses[position]}")
    if position == 7:
        game_state["players"][player]["position"] += 1
    elif position == 14:
        game_state["players"][opponent]["turns_lost"] += 1
    elif position == 25 and game_state["players"][player]["position"] < game_state["players"][opponent]["position"]:
        game_state["players"][player]["position"] += 2
    elif position == 33:
        game_state["current_turn"] = player

def handle_setback(game_state, player, position):
    setbacks = {
        9: "Engine Overheats! Lose a turn.",
        17: "Oil Slick! Move back 2 spaces.",
        27: "Tire Blowout! Lose a turn.",
        38: "Brake Fade! Move back 1 space."
    }
    game_state["event_log"].append(f"{player} landed on a setback space: {setbacks[position]}")
    if position == 9 or position == 27:
        game_state["players"][player]["turns_lost"] += 1
    elif position == 17:
        game_state["players"][player]["position"] -= 2
    elif position == 38:
        game_state["players"][player]["position"] -= 1

def crash(game_state, player1, player2):
    p1_roll = random.randint(1, 6)
    p2_roll = random.randint(1, 6)
    game_state["players"][player1]["position"] -= p1_roll
    game_state["players"][player2]["position"] -= p2_roll

if __name__ == '__main__':
    app.run(debug=True)
