import os
import re
import time
import gradio as gr
from typing import Tuple, List, Optional
from crewai import Agent
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

# Define constants for players
X_PLAYER = "X"
O_PLAYER = "O"
EMPTY = " "

class TicTacToeBoard:
    def __init__(self):
        self.board = [[EMPTY for _ in range(3)] for _ in range(3)]
        self.current_player = X_PLAYER

    def make_move(self, row: int, col: int) -> Tuple[bool, str]:
        """Make a move on the board"""
        if not (0 <= row <= 2 and 0 <= col <= 2):
            return False, "Invalid move: Position out of bounds. Please choose row and column between 0 and 2."

        if self.board[row][col] != EMPTY:
            return False, f"Invalid move: Position ({row}, {col}) is already occupied."

        self.board[row][col] = self.current_player
        board_state = self.get_board_state()
        self.current_player = O_PLAYER if self.current_player == X_PLAYER else X_PLAYER
        return True, f"Move successful!\n{board_state}"

    def get_board_state(self) -> str:
        """Returns a string representation of the current board state"""
        board_str = "\n-------------\n"
        for row in self.board:
            board_str += f"| {' | '.join(row)} |\n-------------\n"
        return board_str

    def get_board_html(self) -> str:
        """Returns HTML representation of the board"""
        html = '<div style="display: grid; grid-template-columns: repeat(3, 100px); gap: 5px; justify-content: center; margin: 20px auto; background: #333; padding: 5px; border-radius: 8px; width: fit-content;">'
        for row in self.board:
            for cell in row:
                color = "#4CAF50" if cell == "X" else "#f44336" if cell == "O" else "#fff"
                html += f'<div style="width: 100px; height: 100px; display: flex; align-items: center; justify-content: center; font-size: 2.5em; font-weight: bold; background-color: #2b2b2b; color: {color}; border-radius: 4px;">{cell}</div>'
        html += '</div>'
        return html

    def check_winner(self) -> Optional[str]:
        """Check if there's a winner"""
        # Check rows
        for row in self.board:
            if row.count(row[0]) == 3 and row[0] != EMPTY:
                return row[0]

        # Check columns
        for col in range(3):
            column = [self.board[row][col] for row in range(3)]
            if column.count(column[0]) == 3 and column[0] != EMPTY:
                return column[0]

        # Check diagonals
        diagonal1 = [self.board[i][i] for i in range(3)]
        if diagonal1.count(diagonal1[0]) == 3 and diagonal1[0] != EMPTY:
            return diagonal1[0]

        diagonal2 = [self.board[i][2 - i] for i in range(3)]
        if diagonal2.count(diagonal2[0]) == 3 and diagonal2[0] != EMPTY:
            return diagonal2[0]

        return None

    def is_board_full(self) -> bool:
        """Check if the board is full"""
        return all(cell != EMPTY for row in self.board for cell in row)

    def get_valid_moves(self) -> List[Tuple[int, int]]:
        """Get a list of valid moves"""
        valid_moves = []
        for row in range(3):
            for col in range(3):
                if self.board[row][col] == EMPTY:
                    valid_moves.append((row, col))
        return valid_moves

    def get_game_state(self) -> Tuple[bool, str]:
        """Get the current game state"""
        winner = self.check_winner()
        if winner:
            return True, f"Player {winner} wins!"
        if self.is_board_full():
            return True, "It's a draw!"
        return False, "Game in progress"

def get_llm_for_model(model_str: str):
    """Get the appropriate LLM for the model string"""
    provider, model_name = model_str.split(":")

    if provider == "openai":
        return ChatOpenAI(model=model_name, temperature=0.7)
    elif provider == "anthropic":
        if "thinking" in model_name:
            # For Claude with thinking
            return ChatAnthropic(
                model="claude-3-7-sonnet-20250219",
                max_tokens=8192,
                temperature=0.7
            )
        else:
            return ChatAnthropic(model=model_name, temperature=0.7)
    elif provider == "google":
        return ChatGoogleGenerativeAI(model=model_name, temperature=0.7)
    elif provider == "groq":
        return ChatGroq(model=model_name, temperature=0.7)
    else:
        raise ValueError(f"Unsupported provider: {provider}")

def create_player_agent(player: str, model_str: str) -> Agent:
    """Create a player agent using CrewAI"""
    llm = get_llm_for_model(model_str)

    description = f"""\
You are Player {player} in a Tic Tac Toe game. Your goal is to win by placing three {player}'s in a row (horizontally, vertically, or diagonally).

BOARD LAYOUT:
- The board is a 3x3 grid with coordinates from (0,0) to (2,2)
- Top-left is (0,0), bottom-right is (2,2)

RULES:
- You can only place {player} in empty spaces (shown as " " on the board)
- Players take turns placing their marks
- First to get 3 marks in a row (horizontal, vertical, or diagonal) wins
- If all spaces are filled with no winner, the game is a draw

YOUR RESPONSE:
- Provide ONLY two numbers separated by a space (row column)
- Example: "1 2" places your {player} in row 1, column 2
- Choose only from the valid moves list provided to you

STRATEGY TIPS:
- Study the board carefully and make strategic moves
- Block your opponent's potential winning moves
- Create opportunities for multiple winning paths
- Pay attention to the valid moves and avoid illegal moves
"""

    agent = Agent(
        role=f"Player {player}",
        goal=f"Win the Tic Tac Toe game by placing three {player}'s in a row",
        backstory=description,
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

    return agent

def make_agent_move(agent: Agent, board: TicTacToeBoard) -> Tuple[bool, str, int, int]:
    """Have the agent make a move"""
    valid_moves = board.get_valid_moves()
    board_state = board.get_board_state()

    prompt = f"""\
Current board state:\n{board_state}\n
Available valid moves (row, col): {valid_moves}\n
Choose your next move from the valid moves above.
Respond with ONLY two numbers for row and column, e.g. "1 2"."""

    try:
        # Use CrewAI agent to get response
        response = agent.llm.invoke(prompt)
        content = response.content if hasattr(response, 'content') else str(response)

        # Parse the response
        numbers = re.findall(r"\d+", content)
        if len(numbers) >= 2:
            row, col = int(numbers[0]), int(numbers[1])
            success, message = board.make_move(row, col)
            return success, message, row, col
        else:
            return False, "Failed to parse move from agent response", -1, -1

    except Exception as e:
        return False, f"Error getting move from agent: {str(e)}", -1, -1

def play_game(model_x: str, model_o: str):
    """Play a full game between two agents"""
    board = TicTacToeBoard()
    player_x = create_player_agent("X", model_x)
    player_o = create_player_agent("O", model_o)

    move_history = []
    board_html = board.get_board_html()

    yield board_html, "Game started!", move_history

    while True:
        game_over, status = board.get_game_state()
        if game_over:
            board_html = board.get_board_html()
            final_status = f"🏆 Game Over! {status}"
            yield board_html, final_status, move_history
            break

        current_agent = player_x if board.current_player == "X" else player_o
        player_name = f"Player {board.current_player} ({model_x.split(':')[1] if board.current_player == 'X' else model_o.split(':')[1]})"

        status_msg = f"🤔 {player_name} is thinking..."
        yield board.get_board_html(), status_msg, move_history

        success, message, row, col = make_agent_move(current_agent, board)

        if success:
            move_history.append({
                "player": player_name,
                "move": f"({row}, {col})",
                "board": board.get_board_state()
            })
            board_html = board.get_board_html()
            status_msg = f"✅ {player_name} placed at ({row}, {col})"
            yield board_html, status_msg, move_history
            time.sleep(0.5)  # Brief pause for visibility
        else:
            status_msg = f"❌ Error: {message}"
            yield board.get_board_html(), status_msg, move_history
            break

def format_move_history(history):
    """Format move history as HTML"""
    if not history:
        return "No moves yet"

    html = '<div style="background: #2b2b2b; padding: 15px; border-radius: 8px; max-height: 400px; overflow-y: auto;">'
    for i, move in enumerate(history, 1):
        color = "#4CAF50" if "X" in move["player"] else "#f44336"
        html += f'<div style="margin: 10px 0; padding: 10px; background: #1e1e1e; border-left: 4px solid {color}; border-radius: 4px;">'
        html += f'<strong>Move #{i}: {move["player"]}</strong><br>'
        html += f'Position: {move["move"]}<br>'
        html += f'</div>'
    html += '</div>'
    return html

def create_interface():
    """Create Gradio interface"""

    model_options = {
        "GPT-4o": "openai:gpt-4o",
        "GPT-4o-mini": "openai:gpt-4o-mini",
        "Claude 3.5 Sonnet": "anthropic:claude-3-5-sonnet-20241022",
        "Claude 3.7 Sonnet": "anthropic:claude-3-7-sonnet-20250219",
        "Gemini 2.0 Flash": "google:gemini-2.0-flash-exp",
        "Llama 3.3 70B": "groq:llama-3.3-70b-versatile",
    }

    with gr.Blocks(title="AI Tic Tac Toe Battle", theme=gr.themes.Soft()) as demo:
        gr.HTML("""
            <div style="text-align: center; background: linear-gradient(45deg, #FF4B2B, #FF416C); padding: 2rem; border-radius: 10px; margin-bottom: 2rem;">
                <h1 style="color: white; margin: 0; font-size: 2.5em;">🎮 AI Tic Tac Toe Battle</h1>
                <p style="color: white; margin-top: 0.5rem;">Watch two AI agents compete in real-time!</p>
            </div>
        """)

        with gr.Row():
            with gr.Column(scale=2):
                board_display = gr.HTML(
                    value='<div style="text-align: center; padding: 40px; color: #888;">Press "Start Game" to begin!</div>',
                    label="Game Board"
                )

                status_display = gr.Textbox(
                    label="Game Status",
                    value="Ready to play!",
                    interactive=False
                )

                with gr.Row():
                    start_btn = gr.Button("▶️ Start New Game", variant="primary", size="lg")
                    stop_btn = gr.Button("⏹️ Stop Game", variant="stop", size="lg")

            with gr.Column(scale=1):
                gr.Markdown("### ⚙️ Game Settings")

                player_x = gr.Dropdown(
                    choices=list(model_options.keys()),
                    value="Claude 3.7 Sonnet",
                    label="Player X (First)",
                    info="Choose model for Player X"
                )

                player_o = gr.Dropdown(
                    choices=list(model_options.keys()),
                    value="GPT-4o",
                    label="Player O (Second)",
                    info="Choose model for Player O"
                )

                gr.Markdown(
                    """
                    ### 📋 Required API Keys
                    Set these in your .env file:
                    - `OPENAI_API_KEY` - For GPT models
                    - `ANTHROPIC_API_KEY` - For Claude models
                    - `GOOGLE_API_KEY` - For Gemini models
                    - `GROQ_API_KEY` - For Llama models

                    ### 🎯 How it Works
                    Each agent analyzes the board and:
                    - 🏆 Finds winning moves
                    - 🛡️ Blocks opponent victories
                    - ⭐ Controls strategic positions
                    - 🤔 Plans multiple moves ahead
                    """
                )

        gr.Markdown("### 📜 Move History")
        history_display = gr.HTML(value="No moves yet")

        # Game state
        game_state = gr.State(None)
        move_history = gr.State([])

        def start_game(p_x, p_o):
            model_x = model_options[p_x]
            model_o = model_options[p_o]

            for board_html, status, history in play_game(model_x, model_o):
                history_html = format_move_history(history)
                yield board_html, status, history_html

        start_btn.click(
            fn=start_game,
            inputs=[player_x, player_o],
            outputs=[board_display, status_display, history_display]
        )

        gr.Examples(
            examples=[
                ["Claude 3.7 Sonnet", "GPT-4o"],
                ["GPT-4o", "Claude 3.5 Sonnet"],
                ["Gemini 2.0 Flash", "Llama 3.3 70B"],
            ],
            inputs=[player_x, player_o]
        )

    return demo

if __name__ == "__main__":
    demo = create_interface()
    demo.launch(share=True)
