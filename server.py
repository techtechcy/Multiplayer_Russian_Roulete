import os
import queue
import socket
import random
import argparse
import platform
import threading
from time import sleep
from shared import ntw
from typing import Literal


parser = argparse.ArgumentParser(description='Russian_Roulette_Server')

parser.add_argument('--chambers', action="store", type=int, default=6)
parser.add_argument('--port', action="store", type=int, default=ntw.default_port)
parser.add_argument("--nogui", action="store_true", help="Disable the gui")
parser.add_argument("--debug", action="store_true", help="Enable debug mode")

fargs = parser.parse_args()



os.system("cls")
q = queue.Queue()

class defaults:
    op_sys: Literal["Linux", "Windows", "Java", ""] = platform.system() # type: ignore
    cls = "cls" if op_sys == "Windows" else "clear"
    game_starting_delay = 5 # in seconds
    delay_to_verify_ready_players = 2 # in seconds
    
class cfg:
    numbers_of_chambers = fargs.chambers
    port = fargs.port
    nogui = fargs.nogui
    debug = fargs.debug

    max_clients = numbers_of_chambers - 1
    

class Gun:
    def __init__(self):
        self.chambers: list[bool] = [False] * cfg.numbers_of_chambers
        self.load_bullet()
        self.spin_chambers()

    def load_bullet(self, bullets: int = 1):
        for i in range(1, bullets + 1):
            bullet_position = random.randint(0, cfg.numbers_of_chambers - 1)
            while self.chambers[bullet_position] == True:
                bullet_position = random.randint(0, cfg.numbers_of_chambers - 1)
            self.chambers[bullet_position] = True
            # really efficient trust
            # fr -enter

    def spin_chambers(self):
        random.shuffle(self.chambers)

    def pull_trigger(self):
        return self.chambers.pop(0)
    
    def clear(self, deadly_bullets: int):
        self.chambers: list[bool] = [False] * cfg.numbers_of_chambers
        self.load_bullet(int(deadly_bullets))
        self.spin_chambers()
        
    @property
    def deadly_bullets(self) -> int:
        i = 0
        for chamber in self.chambers:
            if chamber == True:
                i += 1
        return i
                
    


class _server:
    def __init__(self, port: int = cfg.port):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(("", port))
        self.server_socket.listen(cfg.max_clients)
        print(f"Server listening on port {port}")
        
        self.ready_users = []
        
        
    def start_accepting_connections(self):
        while True:
            client_socket, client_address = self.server_socket.accept()
            client_handler = threading.Thread(target=self.handle_client, args=(client_socket, client_address), daemon=True, name=f"Client-Handler_{client_address[0]}:{client_address[1]}")
            client_handler.start()
            
            
    def broadcast_packet(self, packet: bytes, delay: float = 0.2):
        for user in player_list:
            user.send_packet(packet)   
            sleep(delay)
    
        
    def handle_client(self, client_socket: socket.socket, client_address: tuple):
        print(f"New connection from {client_address[0]}:{client_address[1]}")
        
        packet_queue = []
        should_accept_packets = True

        while should_accept_packets:
            full_packet = ""
            
            try:
                while True:
                    data = client_socket.recv(ntw.max_packet_size)
                    cprint(f"Received Raw Packet: {data.decode()}")
                    
                    if not data:
                        return
                    
                    full_packet += data.decode()
                    
                    if full_packet.startswith(ntw.start) and full_packet.endswith(ntw.end):
                        break
                
                # FULL PACKET
                num_of_packets = full_packet.count(ntw.end) # how many packets does the full packet contain?

                if num_of_packets > 1: # multiple packets
                    cprint("MULTIPLE PACKETS HAVE BEEN RECEIVED")
                    cprint(f"Full Packet: {full_packet}")
                    packet = full_packet
                else: # one packet
                    packet = full_packet
                    pass


                ############# handle packets #############
                packet_type, packet_class, args = ntw.decoding.decode_packet(packet)
                packet_type: str
                packet_class: ntw.packets.general_packet
                has_extra_args = False
            
                if type(args) == list:
                    has_extra_args = True
                    
                
                if packet_type == ntw.packets.heartbeat.RAW:
                    respond_PACKET = ntw.packets.heartbeat_response.encode(len(player_list))
                    cprint(f"Received Heartbeat, responding with {respond_PACKET}")
                    client_socket.send(respond_PACKET)
                
                elif packet_type == ntw.packets.connection.RAW:
                    username = str(args[0])
                    is_valid, error_message, delay = ntw.validate_username(username)
                    if not is_valid:
                        client_socket.send(ntw.packets.invalid_username.encode(error_message, delay))
                    else:
                        player_list.append(client(csocket=client_socket, client_ip=client_address[0], client_port=client_address[1], username=username))
                        cprint(f"User '{username}' connected from {client_address[0]}:{client_address[1]}")
                        
                    
                
                elif packet_type == ntw.packets.readiness.RAW:
                    is_ready = args
                    if is_ready:
                        server.ready_users.append(client_socket)
                        cprint(f"User from {client.get_user_from_ip(client_address[0])} is ready")
                    else:
                        server.ready_users.remove(client_socket)
                        cprint(f"User from {client.get_user_from_ip(client_address[0])} is no longer ready")
                
                elif packet_type == ntw.packets.invalid_packet.RAW:
                    cprint(f"Received invalid packet from client: {args}, {full_packet}")
                    cprint(f"Error: {str(args)}")
                    
                elif packet_type == ntw.packets.request_players.RAW:
                    username_list = []
                    for user in player_list:
                        username_list.append(user.username)
                    cprint(f"Sending Players: {username_list}")
                    client_socket.send(ntw.packets.players.encode(username_list))
                    
                elif packet_type == ntw.packets.user_disconnection.RAW:
                    cprint(f"{client.get_user_from_ip(client_address[0])}: Disconnected Gracefully")
                    try:
                        player_list.remove(client.get_user_from_ip(client_address[0])) # type: ignore
                        client_socket.close()
                        should_accept_packets = False
                        break
                    except:
                        cprint("Cant disconnect player: Player never sent a connection packet")
                
                elif packet_type == ntw.packets.pressed_trigger.RAW:
                    cl = client.get_user_from_ip(client_address[0])
                    if cl and cl.selected:
                        cl.pressed_trigger = True # type: ignore
                        
                    
                    

                    
                
            except Exception as e:
                cprint(f"Error handling client {client_address[0]}:{client_address[1]}:\n{e}")
                print(f"There are {len(player_list)} players connected")
                try:
                    player_list.remove(client.get_user_from_ip(client_address[0])) # type: ignore
                except:
                    cprint("Cant disconnect player: Player never sent a connection packet")
                return


server = _server()
accept_connections_thread = threading.Thread(target=server.start_accepting_connections, daemon=True)

class client:  # type: ignore
    def __init__(self, csocket: socket.socket, client_ip: str, client_port: str, username: str): 
        self.client_ip = client_ip
        self.client_port = client_port
        self.csocket = csocket
        self.username = username
        self.selected = False
        self.alive = True
        self.pressed_trigger = False
        
    @staticmethod
    def get_user_from_ip(client_ip: str):
        for user in player_list:
            if user.client_ip == client_ip:
                return user
        return False
    
    def send_packet(self, data: str | bytes):
        if type(data) == str:
            data = data.encode()
        self.csocket.send(data)  # type: ignore
        
    def select(self):
        self.selected = True
        self.send_packet(ntw.packets.player_selected.encode(self.username))

        while not self.pressed_trigger: # explanation: waiting until the client presses the trigger
            sleep(0.1)
        
        self.pressed_trigger = False
        self.selected = False
    
    def kill(self):
        self.alive = False
        server.broadcast_packet(ntw.packets.player_eliminated.encode(self.username))
    

    

user_with_gun = None
player_list: list[client] = []







if not cfg.nogui:
    import tkinter as tk
    from tkinter import * # type: ignore [wildcard import pylance 🔥]
    from tkinter.ttk import * # type: ignore [w pylance]
    
    class GUI(tk.Frame):

        # This class defines the graphical user interface 

        def __init__(self, parent: tk.Tk, server: _server, *args, **kwargs):
            tk.Frame.__init__(self, parent, *args, **kwargs)
            self.root = parent
            self.build_gui()
        
        def build_gui(self):                    
            # Build GUI
            self.root.title('Packet Testing')
            
            
            def broadcast_game_started_packet():
                print("Broadcasting Game Started Packet...")
                server.broadcast_packet(ntw.packets.game_started.encode())
                
            def broadcast_clear_terminal_packet():
                print("Broadcasting Game Started Packet...")
                server.broadcast_packet(ntw.packets.clear_terminal.encode())
                

            
            
            ################### Buttons ####################
            broadcast_game_started_btn = tk.Button(self.root, text="Broadcast Packet: Game Started", command=broadcast_game_started_packet)
            broadcast_game_started_btn.pack(pady=10)
            
            broadcast_game_started_btn = tk.Button(self.root, text="Broadcast Packet: Clear Terminal", command=broadcast_clear_terminal_packet)
            broadcast_game_started_btn.pack(pady=10)
            ################################################



    def main():
        root = tk.Tk()
        root.geometry("500x500")
        root.wm_attributes("-topmost", True)
        GUI(root, server)

        root.mainloop()


    threading.Thread(target=main, daemon=True).start()
    
    
def cprint(text: str):
    print(f"[SERVER]: {text}")
    

        

    
############################################################### Actual Game ###############################################################
sleep(0.5)
accept_connections_thread.start()
game_has_started = False
os.system(defaults.cls)

def prepare_game():
    global game_has_started
    os.system(defaults.cls)
    print(f"All {len(player_list)} players are ready. Starting the game in {defaults.game_starting_delay} seconds...")
    
    server.broadcast_packet(ntw.packets.game_about_to_start.encode())
    sleep(defaults.game_starting_delay)
    print("Game has started.")
    server.broadcast_packet(ntw.packets.game_started.encode())
    game_has_started = True
    sleep(2)
    os.system(defaults.cls)

    game()

def game():
    """
    The server has started the game, this function handles the game itself
    """ # <- w comment ngl # ENTER WHAT IS THE POINT OF THIS DESCRIPTION AND COMMENT OF A FUNCTION THATS JUST A WHILE LOOP ENTER
    # WAIT A FUCKING MOMENT WHY IS THERE A ENDLESS WHILE LOOP HERE THATS USED
    # oh wait im the one that put it here
    # fuck (-techtech)
    
    gun = Gun()
    turn_order = player_list.copy()
    random.shuffle(turn_order)

    deadly_bullets = gun.deadly_bullets
    
    while True:
        while gun.deadly_bullets > 0:
            for player in turn_order:
                cprint(f"{player.username} has been selected")
                player.select()
                is_dead = gun.pull_trigger()
                
                if is_dead:
                    print("")
                    player.kill()
            gun.clear(deadly_bullets)

print("Server has Started!")
while True:
    if len(server.ready_users) == len(player_list) and len(player_list) >= 2:
        sleep(defaults.delay_to_verify_ready_players)
        if len(server.ready_users) == len(player_list) and len(player_list) >= 2:
            prepare_game()
    sleep(0.5)
       
print("Reached EOF") # idk how the code could possibly reach this part with a while true loop but anyways
sleep(3) # W sleep [100% needed trust 🙏]

# shut the fuck up enter this was before the while loop i think -techtech