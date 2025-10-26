import socket
import random
import typing
from time import sleep
import queue
import threading
from shared import ntw
import os

os.system("cls")
q = queue.Queue()

class defaults:
    port = 8032
    numbers_of_chambers = 6
    max_clients = numbers_of_chambers - 1
    
    
    
    
def cprint(text: str):
    print(f"[CLIENT_THREAD]: {text}")
    
    
    
    
class client:
    def __init__(self, csocket: socket.socket, client_ip: str, client_port: str): 
        self.client_ip = client_ip
        self.client_port = client_port
        self.csocket = csocket
    
    def send_packet(self, data: str | bytes):
        if type(data) == str:
            data = data.encode()
        self.csocket.send(data)
    


    

            


   
user_with_gun = None
user_list: list[client] = []

class Gun:
    def __init__(self):
        self.chambers = [False] * defaults.numbers_of_chambers
        self.load_bullet()
        self.spin_chambers()

    def load_bullet(self):
        bullet_position = random.randint(0, defaults.numbers_of_chambers - 1)
        self.chambers[bullet_position] = True

    def spin_chambers(self):
        random.shuffle(self.chambers)

    def pull_trigger(self):
        return self.chambers.pop(0)
    

class _server:
    def __init__(self, port: int = defaults.port):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(("", port))
        self.server_socket.listen(defaults.max_clients)
        print(f"Server listening on port {port}")
        
        self.ready_users = []
        
        
    def start_accepting_connections(self):
        while True:
            client_socket, client_address = self.server_socket.accept()
            client_handler = threading.Thread(target=self.handle_client, args=(client_socket, client_address))
            client_handler.start()
    
    
        
    def handle_client(self, client_socket: socket.socket, client_address: tuple):
        print(f"New connection from {client_address[0]}:{client_address[1]}")
        
        while True:
            full_packet = ""
            
            try:
                while True:
                    data = client_socket.recv(ntw.max_packet_size)
                    
                    if not data:
                        return
                    
                    full_packet += data.decode()
                    
                    if full_packet.startswith(ntw.start) and full_packet.endswith(ntw.end):
                        cprint(f"Received full packet from client: {full_packet}")
                        break
                
                # FULL PACKET

                packet_type, packet_args = ntw.decoding.decode_packet(full_packet)
                
                if packet_type == ntw.types["heartbeat"]:
                    cprint("Received heartbeat from client")
                    client_socket.send(ntw.encoding.encode_heartbeat_response_packet(len(user_list)))
                
                elif packet_type == ntw.types["connection"]:
                    username = packet_args
                    user_list.append(client(client_socket, client_address[0], client_address[1]))
                    cprint(f"User '{username}' connected from {client_address[0]}:{client_address[1]}")
                    cprint(f"Player List: {user_list}")
                
                elif packet_type == ntw.types["readiness"]:
                    is_ready = packet_args
                    if is_ready:
                        server.ready_users.append(client_socket)
                        cprint(f"User from {client_address[0]}:{client_address[1]} is ready")
                    else:
                        server.ready_users.remove(client_socket)
                        cprint(f"User from {client_address[0]}:{client_address[1]} is no longer ready")
                
                elif packet_type == ntw.types["invalid_packet"]:
                    cprint(f"Received invalid packet from client: {packet_args}, {full_packet}")
                    
                elif packet_type == ntw.types["rq_ply"]:
                    cprint("Sending Players...")
                    client_socket.send(ntw.encoding.encode_players_packet(user_list))
                    
                elif packet_type == ntw.types["user_disconnection"]:
                    cprint(f"{client.get_user_from_ip(client_address[0])}: Disconnected Gracefully")
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                
            except Exception as e:
                cprint(f"Error handling client {client_address[0]}:{client_address[1]}:\n{e}")
                cprint(f"Player List: {user_list}")
                user_list.remove(client.get_user_from_ip(client_address[0]))
                return
            

class client:
    def __init__(self, csocket: socket.socket, client_ip: str, client_port: str): 
        self.client_ip = client_ip
        self.client_port = client_port
        self.csocket = csocket
        
    def _send_packet(self, data: str):
        self.csocket.send(data.encode())
        
    @staticmethod
    def get_user_from_ip(client_ip: str):
        for user in user_list:
            if user.client_ip == client_ip:
                return user
        return False
        


gun = Gun()
server = _server()
accept_connections_thread = threading.Thread(target=server.start_accepting_connections)


    
###################### Game Loop #####################
print("Server has Started!")
input("Press Enter to start accepting connections...")
accept_connections_thread.start()
while True:
    if len(server.ready_users) == len(user_list) and len(user_list) >= 2:
        print("All players are ready. Starting the game in 5 seconds...")
        sleep(5)
        
        for user in user_list:
            user.csocket.send(ntw.encoding.encode_game_started_packet())
            
        
        while True:
            for user in user_list:
                user.sendall(b"It's your turn! Pulling the trigger...\n")
                sleep(2)
                
                if gun.pull_trigger():
                    user.sendall(b"Bang! You are eliminated.\n")
                    user_list.remove(user)
                    server.ready_users.remove(user)
                    
                    if len(user_list) == 1:
                        user_list[0].sendall(b"You are the last player standing! You win!\n")
                        print("Game over. Restarting in 10 seconds...")
                        sleep(10)
                        gun = Gun()
                        break
                else:
                    user.sendall(b"Click! You survived this round.\n")
    sleep(3)
        
    
    
    
    

    
    
        

