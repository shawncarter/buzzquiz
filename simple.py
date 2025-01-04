import pygame
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
ready_players = [False, False, False, False]  # Track which controllers pressed 'red'
selected_players = [False, False, False, False]
score = [0, 0, 0, 0]

players_list = sorted([
    "Cam", "Emily", "Oli", "Anna", "David", "Fran",
    "Billy", "Mary", "Iris", "Gran", "James", "Shawn",
    "Kerry", "Guest 1", "Guest 2"
])

selected_player_index = [-1, -1, -1, -1]  # -1 => not yet selected
used_names = set()

READY_COUNTDOWN_TIME = 5
countdown_started = False
countdown_paused = False
countdown_seconds = READY_COUNTDOWN_TIME

# We'll store the total number of questions here
num_questions = 10
rounds_selected = False

clock = pygame.time.Clock()

# -----------------------------------
# LIGHT BLINK VARIABLES
# -----------------------------------
blink_state = False
last_blink_time = time.time()


# -----------------------------
# LIGHT CONTROL FUNCTIONS
# -----------------------------

def update_lights_ready_screen():
    """
    Updates the lights during the 'Ready' screen:
      - If player i is NOT ready: light ON (steady).
      - If player i IS ready: light BLINK.
    """
    global blink_state, last_blink_time

    if time.time() - last_blink_time >= 0.5:
        blink_state = not blink_state
        last_blink_time = time.time()

    for i in range(4):
        if not ready_players[i]:
            buzz.light_set(i, True)      # Not pressed => ON
        else:
            buzz.light_set(i, blink_state)  # Pressed => BLINK


def update_lights_name_selection():
    """
    During Name Selection:
      - Inactive players => OFF
      - Active but not confirmed => BLINK
      - Active and confirmed => ON
    """
    global blink_state, last_blink_time

    if time.time() - last_blink_time >= 0.5:
        blink_state = not blink_state
        last_blink_time = time.time()

    for i in range(4):
        if not ready_players[i]:
            buzz.light_set(i, False)
        else:
            if not selected_players[i]:
                buzz.light_set(i, blink_state)
            else:
                buzz.light_set(i, True)


def update_lights_round_selection():
    """
    During Round Selection:
      - Inactive players => OFF
      - Active players => BLINK (until round is confirmed)
    """
    global blink_state, last_blink_time

    if time.time() - last_blink_time >= 0.5:
        blink_state = not blink_state
        last_blink_time = time.time()

    for i in range(4):
        if not ready_players[i]:
            buzz.light_set(i, False)
        else:
            # All active controllers blink until a red press finalises the selection
            buzz.light_set(i, blink_state)


# -----------------------------
# DRAW FUNCTIONS
# -----------------------------

def draw_ready_screen():
    """Draws the screen showing which players have pressed the red buzzer and a countdown if started."""
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
    """Draws the name-selection screen, split for each active player."""
    active_players = sum(ready_players) or 1
    screen.fill(WHITE)

    # Title
    title_text = font_large.render("Select Your Name", True, BLACK)
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 20))

    section_width = WIDTH // active_players

    player_slot = 0
    for i in range(4):
        if not ready_players[i]:
            continue

        x_offset = player_slot * section_width
        y_offset = 100
        player_slot += 1

        if selected_players[i]:
            # Player has finalised their choice
            pygame.draw.rect(screen, GREEN, (x_offset, y_offset, section_width, HEIGHT - y_offset))
            chosen_name_text = font_large.render(players_list[selected_player_index[i]], True, BLACK)
            screen.blit(chosen_name_text, (x_offset + (section_width // 2 - chosen_name_text.get_width() // 2),
                                           HEIGHT // 2 - 50))
            ready_text = font_small.render("is Ready to Play!", True, BLACK)
            screen.blit(ready_text, (x_offset + (section_width // 2 - ready_text.get_width() // 2),
                                     HEIGHT // 2 + 10))

            instruction = font_small.render("Press Yellow to Reselect", True, BLACK)
            screen.blit(instruction, (x_offset + (section_width // 2 - instruction.get_width() // 2),
                                      HEIGHT - 70))
        else:
            # Not finalised
            pygame.draw.rect(screen, WHITE, (x_offset, y_offset, section_width, HEIGHT - y_offset))
            for index, name in enumerate(players_list):
                if index == selected_player_index[i]:
                    bg_colour = YELLOW
                else:
                    bg_colour = WHITE

                rect_y = y_offset + (index * 30)
                if rect_y + 30 < HEIGHT:
                    pygame.draw.rect(screen, bg_colour, (x_offset, rect_y, section_width, 30))

                    # If name is taken by someone else, show in RED
                    if name in used_names and index != selected_player_index[i]:
                        name_colour = RED
                    else:
                        name_colour = BLACK

                    name_text = font_small.render(name, True, name_colour)
                    screen.blit(name_text, (x_offset + (section_width // 2 - name_text.get_width() // 2),
                                            rect_y))

    help_text = font_small.render("Use Blue for Up, Orange for Down, Red to Select, Yellow to Reselect", True, BLACK)
    screen.blit(help_text, (WIDTH // 2 - help_text.get_width() // 2, HEIGHT - 30))


def draw_round_selection(num_questions):
    """Draw a screen that asks how many questions in total."""
    screen.fill(WHITE)

    prompt_text = font_large.render("How many questions in total?", True, BLACK)
    screen.blit(prompt_text, (WIDTH // 2 - prompt_text.get_width() // 2, HEIGHT // 2 - 100))

    number_text = font_large.render(str(num_questions), True, BLACK)
    screen.blit(number_text, (WIDTH // 2 - number_text.get_width() // 2, HEIGHT // 2 - 20))

    help_text = font_small.render("Use Blue (Up), Orange (Down), Red to Confirm", True, BLACK)
    screen.blit(help_text, (WIDTH // 2 - help_text.get_width() // 2, HEIGHT - 60))


# -----------------------------
# HELPER FUNCTIONS
# -----------------------------

def wait_for_buzzer_release():
    """
    Ensure all buzzers are released before proceeding,
    so we don't instantly trigger any button checks from a prior press.
    """
    while True:
        all_released = True
        for i in range(4):
            buttons = buzz.get_button_status()[i]
            if any(buttons.values()):
                all_released = False
                break
        if all_released:
            break
        time.sleep(0.1)


def start_countdown():
    """
    Start the countdown in a separate thread.
    Break early if all 4 players become ready.
    """
    global countdown_seconds, countdown_started, countdown_paused
    countdown_started = True
    while countdown_seconds > 0:
        if all(ready_players):
            countdown_paused = True
            break
        countdown_seconds -= 1
        time.sleep(1)


def handle_ready_screen():
    """Players press red to indicate readiness; at least 2 needed to move on."""
    global running

    countdown_thread = None

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Check for red presses
        for i in range(4):
            if not ready_players[i]:
                button = buzz.get_button_pressed(i)
                if button == "red":
                    ready_players[i] = True

        # If 2+ ready and countdown not started, launch countdown
        if sum(ready_players) >= 2 and not countdown_started:
            countdown_thread = threading.Thread(target=start_countdown, daemon=True)
            countdown_thread.start()

        # If all ready, skip countdown
        if all(ready_players) and countdown_started:
            break

        # If countdown ended and we have at least 2 players, move on
        if countdown_started and not countdown_paused and countdown_seconds <= 0:
            if sum(ready_players) >= 2:
                break

        # Update lights
        update_lights_ready_screen()

        # Draw screen
        draw_ready_screen()
        pygame.display.flip()
        clock.tick(30)


def handle_name_selection():
    """Active players choose a name (blue/orange = up/down, red = confirm, yellow = reset)."""
    global selected_player_index, selected_players, used_names

    for i in range(4):
        if ready_players[i]:
            selected_player_index[i] = 0

    while True:
        if all((not ready_players[i]) or selected_players[i] for i in range(4)):
            break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        for i in range(4):
            if not ready_players[i]:
                continue

            button = buzz.get_button_pressed(i)
            if selected_players[i]:
                # If already confirmed name
                if button == "yellow":
                    # Reselect
                    if selected_player_index[i] != -1 and players_list[selected_player_index[i]] in used_names:
                        used_names.discard(players_list[selected_player_index[i]])
                    selected_player_index[i] = 0
                    selected_players[i] = False
            else:
                # Not confirmed name yet
                if button == "blue":
                    selected_player_index[i] = (selected_player_index[i] - 1) % len(players_list)
                    while players_list[selected_player_index[i]] in used_names:
                        selected_player_index[i] = (selected_player_index[i] - 1) % len(players_list)

                elif button == "orange":
                    selected_player_index[i] = (selected_player_index[i] + 1) % len(players_list)
                    while players_list[selected_player_index[i]] in used_names:
                        selected_player_index[i] = (selected_player_index[i] + 1) % len(players_list)

                elif button == "red":
                    chosen_name = players_list[selected_player_index[i]]
                    if chosen_name not in used_names:
                        used_names.add(chosen_name)
                        selected_players[i] = True

                elif button == "yellow":
                    # Reset
                    if players_list[selected_player_index[i]] in used_names:
                        used_names.discard(players_list[selected_player_index[i]])
                    selected_player_index[i] = 0
                    selected_players[i] = False

        # Update lights
        update_lights_name_selection()

        # Draw
        draw_name_selection()
        pygame.display.flip()
        clock.tick(30)


def handle_round_selection():
    """
    Let all active (ready) players change the total number of questions.
    Blue => increment
    Orange => decrement
    Red => confirm (by any active player)
    """
    global num_questions, rounds_selected

    while not rounds_selected:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        # Check each active player's button presses
        for i in range(4):
            if ready_players[i]:
                button = buzz.get_button_pressed(i)
                if button == "blue":
                    num_questions += 1
                    # Optional: limit or wrap
                elif button == "orange":
                    num_questions = max(1, num_questions - 1)  # never go below 1
                elif button == "red":
                    # Confirm selection
                    rounds_selected = True
                    break

        # Update lights (active players blink)
        update_lights_round_selection()

        # Draw screen
        draw_round_selection(num_questions)
        pygame.display.flip()
        clock.tick(30)


# -----------------------------
# MAIN
# -----------------------------
def main():
    handle_ready_screen()
    wait_for_buzzer_release()

    handle_name_selection()
    wait_for_buzzer_release()

    # Now handle round selection
    handle_round_selection()
    wait_for_buzzer_release()

    # Done - just a demonstration end screen
    screen.fill(WHITE)
    final_message = font_large.render(f"All Players Ready! {num_questions} Questions", True, BLACK)
    screen.blit(final_message, (WIDTH // 2 - final_message.get_width() // 2, HEIGHT // 2))
    pygame.display.flip()
    time.sleep(3)

    pygame.quit()


if __name__ == "__main__":
    main()
