import socket
import queue
import time
import os
import sys
import msvcrt
import threading
from shared import ntw
import time
import threading
from shared import myGUI
import tkinter as tk
from collections import Counter

gun_texture = "▄︻テ══━一"
gun_effect = "💥"

q = queue.Queue()
logger = queue.Queue()


def get_public_servers() -> list[tuple]: # hard coded 'for now' because im lazy (-techtech)
    """Returns a list of tuples:
    [(server_ip, server_port, server_name)]"""
    return [("85.132.234.152", 2046, "EU Lobby #1")]


def main():
    root = tk.Tk()
    root.wm_attributes("-topmost", True)
    myGUI(root)

    t1 = threading.Thread(target=myGUI.worker, args=[logger])
    t1.start()

    root.mainloop()
    t1.join()

logging_window = threading.Thread(daemon=True, target=main, name="Client Logging Window")
logging_window.start()

def log(msg):
    logger.put_nowait(msg)

class defaults:
    GAME_NAME_NS = "MP_Russian_Roulette"
    GAME_NAME_WS = "Multiplayer Russian Roulette"

def clear_console():
    stop_all_printfs()
    if sys.stdout.isatty():
        print("\033[2J\033[H", end="")
    else:
        print("\n" * 100)

def format_list(list: list | tuple):
    return str(list).replace("[", "").replace("]", "")

_active_printfs = set()
_active_lock = threading.Lock()
is_running = threading.Event()

def stop_all_printfs():
    with _active_lock:
        for flag in list(_active_printfs):
            flag.set()
        _active_printfs.clear()

def printf(text: str, delay: float = 0.06, newline: bool = True, finaldelay: float | None = None):
    stop_all_printfs()

    cancel_flag = threading.Event()
    with _active_lock:
        _active_printfs.add(cancel_flag)

    text_list = list(text)

    for char in text:
        if cancel_flag.is_set():
            break
        print(char, end="", flush=True)
        text_list.remove(char)
        time.sleep(delay)

        should_break = False
        while msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b'\r':
                print("".join(char2 for char2 in text_list), end="", flush=True)
                should_break = True
                break

        if should_break or cancel_flag.is_set():
            break

    if newline:
        print("\n", end="", flush=True)

    if finaldelay:
        time.sleep(finaldelay)
        while msvcrt.kbhit():
            msvcrt.getch()

    with _active_lock:
        _active_printfs.discard(cancel_flag)
            
is_running.set()
csocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

class server:
    def connect_to_server(self, ip: str, port: int) -> bool:
        log(f"Establishing connection with {ip}:{str(port)}")
        printf("Establishing connection...", delay=0.04)
        
        try:
            csocket.connect((ip, port))
        except socket.timeout:
            log(f"Connection failed: Connection Timeout")
            printf("Connection timed out, please try again", delay=0.04, finaldelay=1.25)
        except socket.gaierror:
            log(f"Connection failed: Invalid Hostname or IP Address")
            printf("Invalid hostname or IP address - did you type in the ip and port correctly?", delay=0.04, finaldelay=1.25)
        except OSError as e:
            log(f"Connection failed: OS/Network Error")
            printf("Couldn't connect to the server due to an os or network error - did you type in the ip and port correctly?", delay=0.04, finaldelay=1.25)
        except:
            log(f"Connection failed: Unknown Error")
            printf("Unknown error, please try again", delay=0.04, finaldelay=1.25)
        else:
            log(f"Established a connection with {ip}:{str(port)} successfully")
            printf("Established a connection with the server successfully")
            return True
        return False
    
    def send_packet(self, data: str):
        try:
            csocket.sendall(data.encode())
            return True
        except Exception as e:
            printf("Failed to send packet!", finaldelay=2)
            return False

if not sys.platform.startswith("win"):
    printf("This code runs on windows only", finaldelay=2)
    is_running.clear()
    sys.exit(0)

printf("Welcome to Shut Roulette!")
time.sleep(0.5)
printf("----------------------------------------------", delay=0.01, newline=True)
printf("Available Servers:")

servers = get_public_servers()

# Print the server list
for index, (_, _, server_name) in enumerate(servers, start=1):
    printf(f"{index}. {server_name}", delay=0.04, newline=True)


choice = input("Select a server by number (or press Enter to enter manually): ").strip()

if choice.isdigit() and 1 <= int(choice) <= len(servers):
    selected_server = servers[int(choice) - 1]
    server_ip_input, server_port_input, _ = selected_server
    printf(f"Selected: {selected_server[2]} ({server_ip_input}:{server_port_input})")
else:
    server_ip_input = input(
        f"Enter server IP address (press Enter for default IP: {ntw.default_host}): "
    ) or str(ntw.default_host)

    server_port_input = None
    while server_port_input is None:
        inp = input(
            f"Enter server port (press Enter for default port: {ntw.default_port}): "
        ) or str(ntw.default_port)

        try:
            inted = int(inp)
        except ValueError:
            printf("Invalid server port input")
            server_port_input = None
        else:
            server_port_input = inted

connection_server = server()

player_count = 0
players = []

started = False
about_to_start = False
ready = False

def send_hb():
    global connected, csocket
    while connected:
        q.put(ntw.packets.heartbeat.encode())
        time.sleep(3)

def handle_queue():
    global connected, csocket
    while connected:
        try:
            packet = q.get()  # blocking wait for next packet
            log("OUTGOING: " + packet.decode())
            csocket.send(packet)
        except (socket.error, OSError) as e:
            print("Socket error:", e)
            connected = False
            break
        except Exception as e:
            print("Unexpected error in sendall:", e)
            connected = False
            break

        time.sleep(0.1)


    try:
        if connected:
            csocket.send(ntw.packets.user_disconnection.encode())
        csocket.close()
    except Exception:
        pass
    printf("Disconnected from server")
    

def recv():
    global connected, csocket, players, player_count, started, about_to_start

    while connected:
        buffer = ""
        while is_running.is_set(): # if the is_running event is true
            csocket.settimeout(None)
            
            try:
                response = csocket.recv(ntw.max_packet_size)
            except:
                printf("Connection with the server has been terminated")
                sys.exit(0)

            if not response:
                connected = False
                printf("Server has closed the connection")
                if connected:
                    csocket.send(ntw.packets.user_disconnection.encode())
                csocket.close()
                return

            buffer += response.decode()

            if buffer.startswith(ntw.start) and buffer.find(ntw.end) != -1:
                break
            
        while buffer.find(ntw.start) != -1 and buffer.find(ntw.end) != -1:
            start_index = buffer.find(ntw.start)
            end_index = buffer.find(ntw.end)

            if start_index == -1 or end_index == -1 or end_index < start_index:
                # No full packet yet — wait for more data
                break

            # Extract the packet including start/end
            full_packet = buffer[start_index:end_index + len(ntw.end)]

            # Remove the processed packet from the buffer
            buffer = buffer[end_index + len(ntw.end):]
            
            handle_packet(full_packet)
            
        
        
def handle_packet(packet):
    global player_count
    log("INCOMING: " + packet)
    packet_type, packet_class, args = ntw.decoding.decode_packet(packet)
    packet_type: str
    packet_class: ntw.packets.general_packet
    args: list[str]
    
    
    if packet_type == ntw.packets.heartbeat_response.RAW:
        old_player_count = player_count
        player_count = int(args[0])

        if old_player_count != player_count:
            q.put(ntw.packets.request_players.encode())
        
    elif packet_type == ntw.packets.game_about_to_start.RAW:
        global about_to_start
        about_to_start = True

        clear_console()
        printf("Game is about to start...", delay=0.03)

    elif packet_type == ntw.packets.game_started.RAW:
        global started
        started = True
    
    elif packet_type == ntw.packets.players.RAW:
        global players
        players = args
    
    elif packet_type == ntw.packets.message_to_print.RAW:
        output = str(args[0])
        printf(output, delay=0.03)
    
    elif packet_type == ntw.packets.player_selected.RAW:
        clear_console()
        user_selected = str(args[0])

        printf("The silence fills the room...", delay=0.03, finaldelay=0.8)
        
        if user_selected == username: # YOU HAVE BEEN SELECTED
            printf(f"The gun is being handed to you...", delay=0.03, finaldelay=0.2)

            printf("The cold steel rests against your arm. Your pulse quickens — a single click could decide your fate", delay=0.04, finaldelay=0.2)
            printf("The cylinder clicks into place...", delay=0.04, finaldelay=0.2)
            printf("Sweat drips...", delay=0.05, finaldelay=0.2)
            printf("Fate whispers your name...", delay=0.04, finaldelay=0.2)
            printf("Hit Enter to press the trigger... if you dare...", delay=0.04, newline=False)

            inp = input() # waiting for the user to press THE KEY enter

            printf("For a heartbeat, the world stops...", delay=0.06, finaldelay=0.2)
            printf("Is it over... or has fate spared you this time?", delay=0.06, finaldelay=0.2)

            q.put(ntw.packets.pressed_trigger.encode())
        
        else: # ANOTHER PERSON HAS BEEN SELECTED
            printf(f"The room has gone silent while staring at {user_selected} as the gun was being handed to them...", delay=0.03)
    
    elif packet_type == ntw.packets.clear_terminal.RAW:
        clear_console()

def esc_kb():
    while msvcrt.kbhit():
        if msvcrt.getch() == b"esc":
            if connected:
                try:
                    csocket.send(ntw.packets.user_disconnection.encode())
                except:
                    pass

                sys.exit(0)
        time.sleep(0.1)

threading.Thread(target=esc_kb, daemon=True).start()

username = ""
is_valid = False

while not is_valid:
    printf("What username do you want? (20 characters max, cannot contain: , [ ] |   ): ", newline=False, delay=0.02)
    username = str(input()).replace(" ", "-") or " "

    is_valid, reason_of_invalidation, text_delay = ntw.validate_username(username)
    if not is_valid:
        printf(reason_of_invalidation, text_delay)

connected = connection_server.connect_to_server(server_ip_input, server_port_input)

if not connected:
    is_running.clear()
    csocket.close()
    sys.exit(0)

handle_queue_thread = threading.Thread(target=handle_queue, daemon=True)
handle_queue_thread.start()

recv_thread = threading.Thread(target=recv, daemon=True)
recv_thread.start()

def show_pregame_menu():
    if not started and not about_to_start and connected:
        clear_console()
        print("Write an action (number):\n1) Ready/Unready\n2) List Players In Lobby\n3) List Player Count\n4) Leave & Quit Game")

time.sleep(2)
if connected:
    clear_console()
    q.put(ntw.packets.connection.encode(username))
    threading.Thread(target=send_hb, daemon=True).start()

    printf("Write an action (number):\n1) Ready/Unready\n2) List Players In Lobby\n3) List Player Count\n4) Leave & Quit Game", delay=0.02)
    while not started and connected and not about_to_start:
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b'1':
                ready = not ready
                q.put(ntw.packets.readiness.encode(ready))
                printf("You are " + ("ready" if ready else "no longer ready"), finaldelay=2)
                show_pregame_menu()
            elif key == b'2':
                printf("".join(f"{index + 1}. {plrname}\n" for index, plrname in enumerate(players)), finaldelay=3, newline=False)
                show_pregame_menu()
            elif key == b'3':
                printf(f"{player_count} Player{"s" if player_count > 1 else ""} in this lobby", finaldelay=3)
                show_pregame_menu()
            elif key == b'4':
                printf("Exiting...", finaldelay=1.5)
                is_running.clear()
                if connected:
                    csocket.send(ntw.packets.user_disconnection.encode())
                csocket.close()
                sys.exit(0)
        time.sleep(0.01)
    
    if about_to_start and not started:
        while not started:
            time.sleep(0.01)
        
    if started: ############### Start Game ###############
        printf("The game has started!", delay=0.03, finaldelay=0.4)
        clear_console()

        while started:
            time.sleep(0.5)
