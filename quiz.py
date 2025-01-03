import pygame
import random
import threading
import time
from BuzzController import BuzzController

pygame.init()

# -----------------------------
# SCREEN & COLOURS
# -----------------------------
infoObject = pygame.display.Info()
WIDTH, HEIGHT = infoObject.current_w, infoObject.current_h

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Quiz Game")

# -----------------------------
# FONTS
# -----------------------------
font_large = pygame.font.Font(None, 74)
font_small = pygame.font.Font(None, 36)

# -----------------------------
# BUZZ CONTROLLER
# -----------------------------
buzz = BuzzController()

# -----------------------------
# GAME VARIABLES
# -----------------------------
running = True
ready_players = [False, False, False, False]  # Track which controllers have pressed 'red'
selected_players = [False, False, False, False]
score = [0, 0, 0, 0]

# Pre-sorted list of potential player names
players_list = sorted([
    "Cam", "Emily", "Oli", "Anna", "David", "Fran",
    "Billy", "Mary", "Iris", "Gran", "James", "Shawn",
    "Kerry", "Guest 1", "Guest 2"
])

# Store the selected name index for each controller (-1 means no selection yet)
selected_player_index = [-1, -1, -1, -1]

# Keep track of which names are already taken
used_names = set()

# For our demonstration, 5 seconds countdown (can be changed to 30 for real play)
READY_COUNTDOWN_TIME = 5

countdown_started = False
countdown_paused = False
countdown_seconds = READY_COUNTDOWN_TIME

clock = pygame.time.Clock()

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def draw_ready_screen():
    """Draws the ready screen, showing which players have pressed the red buzzer and a countdown if started."""
    screen.fill(WHITE)

    # Title
    title_text = font_large.render("Press Red to Get Ready!", True, BLACK)
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 20))

    # Draw sections for each player
    section_width = WIDTH // 4
    for i in range(4):
        colour = GREEN if ready_players[i] else RED
        pygame.draw.rect(screen, colour, (i * section_width, 100, section_width, HEIGHT - 100))
        label = font_small.render(f"Player {i + 1}", True, BLACK)
        screen.blit(label, (i * section_width + (section_width // 2 - label.get_width() // 2),
                            HEIGHT // 2))

    # If countdown has started, display it
    if countdown_started and not countdown_paused:
        countdown_text = font_small.render(f"Countdown: {countdown_seconds} sec", True, BLACK)
        screen.blit(countdown_text, (WIDTH // 2 - countdown_text.get_width() // 2, HEIGHT - 50))


def draw_name_selection():
    """Draws the name-selection screen, split according to the number of players who are ready."""
    # Count how many players are actually ready
    active_players = sum(ready_players)
    if active_players == 0:
        active_players = 1  # Just to avoid division-by-zero, though it shouldn't happen

    screen.fill(WHITE)

    # Title
    title_text = font_large.render("Select Your Name", True, BLACK)
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 20))

    section_width = WIDTH // active_players

    # For each ready player, show their selection area
    player_slot = 0
    for i in range(4):
        if not ready_players[i]:
            continue  # skip non-ready players

        x_offset = player_slot * section_width
        y_offset = 100
        player_slot += 1

        # If the player has finalised their choice
        if selected_players[i]:
            # Draw a green block
            pygame.draw.rect(screen, GREEN, (x_offset, y_offset, section_width, HEIGHT - y_offset))
            # Print the chosen name
            chosen_name_text = font_large.render(players_list[selected_player_index[i]], True, BLACK)
            screen.blit(chosen_name_text, (x_offset + (section_width // 2 - chosen_name_text.get_width() // 2),
                                           HEIGHT // 2 - 50))
            ready_text = font_small.render("is Ready to Play!", True, BLACK)
            screen.blit(ready_text, (x_offset + (section_width // 2 - ready_text.get_width() // 2),
                                     HEIGHT // 2 + 10))

            # Instruction to reselect
            instruction = font_small.render("Press Yellow to Reselect", True, BLACK)
            screen.blit(instruction, (x_offset + (section_width // 2 - instruction.get_width() // 2),
                                      HEIGHT - 70))
        else:
            # Draw a white block
            pygame.draw.rect(screen, WHITE, (x_offset, y_offset, section_width, HEIGHT - y_offset))

            # Loop through players_list and highlight the currently selected player in YELLOW
            for index, name in enumerate(players_list):
                # Highlight if it's the current selection
                if index == selected_player_index[i]:
                    bg_colour = YELLOW
                else:
                    bg_colour = WHITE

                rect_y = y_offset + (index * 30)
                if rect_y + 30 < HEIGHT:  # ensure names stay on screen
                    pygame.draw.rect(screen, bg_colour, (x_offset, rect_y, section_width, 30))

                    # If this name is already used by someone else, render it in RED
                    if name in used_names and index != selected_player_index[i]:
                        name_colour = RED
                    else:
                        name_colour = BLACK

                    name_text = font_small.render(name, True, name_colour)
                    screen.blit(name_text, (x_offset + (section_width // 2 - name_text.get_width() // 2),
                                            rect_y))

    # Help text
    help_text = font_small.render("Use Blue for Up, Orange for Down, Red to Select, Yellow to Reselect", True, BLACK)
    screen.blit(help_text, (WIDTH // 2 - help_text.get_width() // 2, HEIGHT - 30))


def wait_for_buzzer_release():
    """
    Ensure all buzzers are released before proceeding,
    so we don't instantly trigger any button checks from a prior press.
    """
    while True:
        all_released = True
        for i in range(4):
            buttons = buzz.get_button_status()[i]  # dictionary of button states
            if any(buttons.values()):
                all_released = False
                break
        if all_released:
            break
        time.sleep(0.1)


def start_countdown():
    """
    Start the countdown in a separate thread.
    If at any point all 4 players become ready, we stop early.
    Otherwise, we count down from the set number of seconds.
    """
    global countdown_seconds, countdown_started, countdown_paused
    countdown_started = True
    while countdown_seconds > 0:
        # If all 4 players are ready, break out of the countdown
        if all(ready_players):
            countdown_paused = True
            break

        # Decrement countdown
        countdown_seconds -= 1
        time.sleep(1)


def handle_ready_screen():
    """
    Handle the first screen logic. We need at least 2 players to press red to start the countdown.
    If the countdown ends OR all 4 players have pressed ready, move on.
    """
    global running

    # Thread for countdown (will only run once 2 players are ready)
    countdown_thread = None

    while running:
        # Event loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Check button presses from the Buzz controllers
        # We only care about 'red' for getting ready
        for i in range(4):
            if not ready_players[i]:
                button = buzz.get_button_pressed(i)
                if button == "red":
                    ready_players[i] = True

        # If we have 2 players ready and countdown not started, start it
        if sum(ready_players) == 2 and not countdown_started:
            countdown_thread = threading.Thread(target=start_countdown, daemon=True)
            countdown_thread.start()

        # If we have 3 players ready and countdown not started, also start it
        if sum(ready_players) == 3 and not countdown_started:
            countdown_thread = threading.Thread(target=start_countdown, daemon=True)
            countdown_thread.start()

        # If we've started counting down or are already in that phase
        # and have 4 ready, we can skip the countdown
        if all(ready_players) and countdown_started:
            break

        # If the countdown ends and we have at least 2 players, we move on
        if countdown_started and not countdown_paused and countdown_seconds <= 0:
            if sum(ready_players) >= 2:
                # Move on
                break

        draw_ready_screen()
        pygame.display.flip()
        clock.tick(30)


def handle_name_selection():
    """
    Let each ready player select a name from the list.
    Use Blue for Up, Orange for Down, Red to confirm, Yellow to reset.
    """
    global selected_player_index, selected_players, used_names

    # Initialise each ready player's selection to 0, or an available index
    for i in range(4):
        if ready_players[i]:
            selected_player_index[i] = 0

    while True:
        # If all ready players have finalised their selection, break
        if all((not ready_players[i]) or selected_players[i] for i in range(4)):
            break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        # Check each ready player's button press
        for i in range(4):
            if not ready_players[i]:
                continue

            button = buzz.get_button_pressed(i)
            
            # -----------------------------------
            # If the player has already confirmed their name
            # -----------------------------------
            if selected_players[i]:
                if button == "yellow":
                    # Allow reselection: discard old name, reset
                    if selected_player_index[i] != -1 and players_list[selected_player_index[i]] in used_names:
                        used_names.discard(players_list[selected_player_index[i]])
                    selected_player_index[i] = 0
                    selected_players[i] = False
                # If they do not press yellow, we do nothing else
                # so they remain locked in
            else:
                # -----------------------------------
                # If the player has not yet confirmed their name
                # -----------------------------------
                if button == "blue":
                    # Move selection up
                    selected_player_index[i] = (selected_player_index[i] - 1) % len(players_list)
                    # Keep skipping over used names
                    while players_list[selected_player_index[i]] in used_names:
                        selected_player_index[i] = (selected_player_index[i] - 1) % len(players_list)

                elif button == "orange":
                    # Move selection down
                    selected_player_index[i] = (selected_player_index[i] + 1) % len(players_list)
                    # Keep skipping over used names
                    while players_list[selected_player_index[i]] in used_names:
                        selected_player_index[i] = (selected_player_index[i] + 1) % len(players_list)

                elif button == "red":
                    # Confirm selection if it's not taken
                    chosen_name = players_list[selected_player_index[i]]
                    if chosen_name not in used_names:
                        used_names.add(chosen_name)
                        selected_players[i] = True

                elif button == "yellow":
                    # If they press yellow but haven't locked a name yet,
                    # just reset to the first available name
                    if players_list[selected_player_index[i]] in used_names:
                        used_names.discard(players_list[selected_player_index[i]])
                    selected_player_index[i] = 0
                    selected_players[i] = False

        draw_name_selection()
        pygame.display.flip()
        clock.tick(30)



def main():
    # Handle the 'Ready' screen
    handle_ready_screen()
    wait_for_buzzer_release()

    # Move on to name selection
    handle_name_selection()
    wait_for_buzzer_release()
    time.sleep(3)
    
    # Final screen
    screen.fill(WHITE)
    final_message = font_large.render("All Players Ready!", True, BLACK)
    screen.blit(final_message, (WIDTH // 2 - final_message.get_width() // 2, HEIGHT // 2))
    pygame.display.flip()
    time.sleep(3)

    pygame.quit()


if __name__ == "__main__":
    main()
