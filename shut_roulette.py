import socket
import queue
import time
import os
import sys
import playsound
import pyvolume
import msvcrt
import threading
from shared import ntw

q = queue.Queue()
os.system("cls")

class defaults:
    GAME_NAME_NS = "MP_Russian_Roulette"
    GAME_NAME_WS = "Multiplayer Russian Roulette"
    CLS = "cls"

def format_list(list: list | tuple):
    return str(list).replace("[", "").replace("]", "")

def printf(text: str, delay: float = 0.06, newline: bool = True, finaldelay: float | None = None):
    text_list = list(text)

    for char in text:
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
        
        
        if should_break:
            break
    
    if newline:
        print("\n", end="", flush=True)
    
    if finaldelay:
        time.sleep(finaldelay)

        while msvcrt.kbhit():
            msvcrt.getch()
            
game_is_running = True

csocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

class server:
    def connect_to_server(self, ip: str, port: int) -> bool:
        printf("Establishing connection...", delay=0.04)
        
        try:
            csocket.connect((ip, port))
        except socket.timeout:
            printf("Connection failed: timed out", delay=0.04)
        except socket.gaierror:
            printf("Invalid hostname or IP address - did you type in the ip and port correctly?", delay=0.04)
        except OSError as e:
            printf("OS or Network Error", delay=0.04)
        except:
            printf("Unknown error, please try again", delay=0.04)
        else:
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
    printf("This code runs on windows only lil nigga", finaldelay=2)
    game_is_running = False
    sys.exit(0)

printf("Welcome to Shut Roulette!")
time.sleep(0.5)
printf("----------------------------------------------", delay=0.01, newline=True)

server_ip_input = input("Enter server IP address: ") or "localhost"
server_port_input = None

while server_port_input == None:
    inp = input("Enter server port (press Enter for default port: 8032): ") or "8032"

    try:
        inted = int(inp)
    except:
        server_port_input = None
        printf("Invalid server port input")
    else:
        server_port_input = inted

gun_texture = "▄︻テ══━一"
gun_effect = "💥"

connection_server = server()

player_count = 0
players = []

started = False
ready = False

def send_hb():
    global connected, csocket
    while connected:
        q.put(ntw.encoding.encode_heartbeat_packet())
        time.sleep(3)

def sendall():
    global connected, csocket
    while connected:
        try:
            packet = q.get()  # blocking wait for next packet
            csocket.send(packet)
            
            # # Handle heartbeat acknowledgment
            # if packet == ntw.encoding.encode_heartbeat_packet():
            #     csocket.settimeout(3.0)  # prevent infinite blocking
            #     ack_response = None

            #     try:
            #         ack_response = csocket.recv(ntw.max_packet_size)
            #     except socket.timeout:
            #         print("Heartbeat ACK timeout:", ack_response)
            #         connected = False
            #         break

            #     decoded = ntw.decoding.decode_packet(ack_response)
            #     if not decoded:
            #         print("Invalid ACK packet")
            #         connected = False
            #         break

            #     packet_type = decoded[0]
            #     if packet_type != ntw.types["heartbeat_response"]:
            #         print("Unexpected heartbeat response: Packet: ", ack_response)
            #         connected = False
            #         break

            #     # Reset timeout after successful ACK
            #     csocket.settimeout(None)

        except (socket.error, OSError) as e:
            print("Socket error:", e)
            connected = False
            break
        except Exception as e:
            print("Unexpected error in sendall:", e)
            connected = False
            break

    try:
        csocket.send(ntw.encoding.encode_user_disconnection())
        csocket.close()
    except Exception:
        pass
    printf("Disconnected from server")

def recv():
    global connected, csocket, players

    while connected:
        buffer = ""
        while game_is_running:
            csocket.settimeout(None)
            response = csocket.recv(ntw.max_packet_size)

            if not response:
                connected = False
                printf("Server has closed the connection")
                csocket.send(ntw.encoding.encode_user_disconnection())
                csocket.close()
                return

            buffer += response.decode()

            if buffer.startswith(ntw.start) and buffer.endswith(ntw.end):
                break

        packet_type, args = ntw.decoding.decode_packet(buffer)
        
        if packet_type == ntw.types["heartbeat_response"]:
            global player_count

            old_player_count = player_count
            player_count = args

            if old_player_count != player_count:
                q.put(ntw.encoding.encode_request_players_packet())
            
        elif packet_type ==  ntw.types["game_started"]:
            global started
            started = True
            printf("The game has started!", delay=0.04)
        
        elif packet_type == ntw.types["players"]:
            print(players)
            players = args

def validate_username(username: str) -> bool:
    valid_user = "".join(char for char in username if char.isalnum())
    return (valid_user == username and len(valid_user) == len(username) and len(valid_user) >= 1 and len(valid_user) <= 20)

valid_username = False

while not valid_username:
    printf("What will you be your username? (1 to 20 alphanumeric characters): ", newline=False, delay=0.04)
    username = str(input()) or " "

    valid_username = validate_username(username)
    if not valid_username:
        printf("Username is invalid!")
    
connected = connection_server.connect_to_server(server_ip_input, server_port_input)

if not connected:
    csocket.send(ntw.encoding.encode_user_disconnection())
    csocket.close()
    game_is_running = False
    sys.exit(0)

threading.Thread(target=sendall, daemon=True).start()
threading.Thread(target=recv, daemon=True).start()

time.sleep(2)
if connected:
    os.system("cls")
    q.put(ntw.encoding.encode_connection_packet(username))
    threading.Thread(target=send_hb, daemon=True).start()

    while connected:
        printf("Write an action (number):\n1) Ready/Unready\n2) List Players In Lobby\n3) List Player Count\n4) Leave & Quit Game", delay=0.03)
        
        while not started and connected:
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key == b'1':
                    ready = not ready
                    q.put(ntw.encoding.encode_readiness_packet(ready))
                elif key == b'2':
                    printf("".join(f"{index + 1}. {plrname}" for index, plrname in enumerate(players)))
                elif key == b'3':
                    printf(f"{player_count} Players in this lobby: {players}")
                elif key == b'4':
                    printf("Exiting...", finaldelay=1.5)
                    csocket.send(ntw.encoding.encode_user_disconnection())
                    csocket.close()
                    game_is_running = False
                    sys.exit(0)

            time.sleep(0.01)
        
        if started:
            ############### start game logic ###############
            pass
