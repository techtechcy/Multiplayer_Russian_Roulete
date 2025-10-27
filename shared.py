import os
import queue
import typing
import inspect
import logging
import datetime
import threading

##################################################### Logging Window ('borrowed' from stackoverflow) #####################################################
import tkinter as tk
import tkinter.scrolledtext as ScrolledText

class TextHandler(logging.Handler):
    # This class allows you to log to a Tkinter Text or ScrolledText widget
    # Adapted from Moshe Kaplan: https://gist.github.com/moshekaplan/c425f861de7bbf28ef06

    def __init__(self, text):
        # run the regular Handler __init__
        logging.Handler.__init__(self)
        # Store a reference to the Text it will log to
        self.text = text

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text.configure(state='normal')
            self.text.insert(tk.END, msg + '\n')
            self.text.configure(state='disabled')
            # Autoscroll to the bottom
            self.text.yview(tk.END)
        # This is necessary because we can't modify the Text from other threads
        self.text.after(0, append)
        
        
class cfg:
    should_crash = True

class myGUI(tk.Frame):

    # This class defines the graphical user interface 

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.root = parent
        self.build_gui()

    def build_gui(self):                    
        # Build GUI
        self.root.title('TEST')
        self.root.option_add('*tearOff', 'FALSE')
        self.grid(column=0, row=0, sticky='ew')
        self.grid_columnconfigure(0, weight=1, uniform='a')
        self.grid_columnconfigure(1, weight=1, uniform='a')
        self.grid_columnconfigure(2, weight=1, uniform='a')
        self.grid_columnconfigure(3, weight=1, uniform='a')

        # Add text widget to display logging info
        st = ScrolledText.ScrolledText(self, state='disabled')
        st.configure(font='TkFixedFont')
        st.grid(column=0, row=1, sticky='w', columnspan=4)

        # Create textLogger
        text_handler = TextHandler(st)

        # Logging configuration
        logging.basicConfig(filename='test.log',
            level=logging.INFO, 
            format='%(asctime)s - %(levelname)s - %(message)s')        

        # Add the handler to logger
        logger = logging.getLogger()        
        logger.addHandler(text_handler)

    @staticmethod
    def worker(logger: queue.Queue):
        # Skeleton worker function, runs in separate thread
        while True:
            time = f"{datetime.datetime.now().hour}:{datetime.datetime.now().minute}:{datetime.datetime.now().second}"
            raw_msg = logger.get()
            msg = f"{time}: {raw_msg}"
            
            logging.info(msg)
            
            
#####################################################################################################################################################



class ntw:
    default_port = 2046
    default_host = "localhost"
    
    start = "(*"
    sep = ","
    end = "*)"
    types = {
        "heartbeat": "hbt",
        "heartbeat_response": "hbt_rsp", # acts as ACK and sends player count
        "connection": "con",
        "readiness": "rdy",
        "invalid_packet": "inv",
        "request_players": "rq_ply",
        "players": "plrs",
        "game_started": "gm_strt",
        "game_about_to_start": "gm_abtstr",
        "pressed_trigger": "prs_trg",
        "player_eliminated": "ply_elim",
        "user_disconnection": "usr_dsc",
        "message_to_print": "msg_prt",
        "player_selected": "ply_sel", # sends what player was selected
        "clear_terminal": "clr_term"
    }
    
    max_packet_size = 1024
    arg_list_sep = "|l|"
    
    
    class InvalidPacket(Exception):
        """Exception raised when a packet is invalid and unable to be decoded/encoded"""
        def __init__(self, message, packet_type: str, location: str):
            super().__init__(message)
            self.packet_type = packet_type
            self.location = location

        def __str__(self):
            return f"Invalid Packet exception at '{self.location}': (Packet Type: {self.packet_type}): {self.message}"
        
    @staticmethod
    def get_current_line_for_errors():
        frame = inspect.currentframe().f_back
        file_name = os.path.basename(frame.f_code.co_filename)
        func_name = frame.f_code.co_name
        line_number = frame.f_lineno
        return f"Line {line_number}, Function {func_name}, File {file_name}"
    
    
    class encoding:
        @staticmethod
        def encode_heartbeat_packet() -> bytes:
            return (ntw.start + ntw.sep + ntw.types["heartbeat"] + ntw.sep + ntw.end).encode()
        
        @staticmethod
        def encode_heartbeat_response_packet(player_count: int) -> bytes:
            return (ntw.start + ntw.sep + ntw.types["heartbeat_response"] + ntw.sep + str(player_count) + ntw.sep + ntw.end).encode()
        
        @staticmethod
        def encode_connection_packet(username: str) -> bytes:
            return (ntw.start + ntw.sep + ntw.types["connection"] + ntw.sep + username + ntw.sep + ntw.end).encode()
        
        @staticmethod
        def encode_readiness_packet(is_ready: bool) -> bytes:
            readiness_str = "1" if is_ready else "0"
            return (ntw.start + ntw.sep + ntw.types["readiness"] + ntw.sep + readiness_str + ntw.sep + ntw.end).encode()
        
        @staticmethod
        def encode_invalid_packet() -> bytes:
            return (ntw.start + ntw.sep + ntw.types["invalid_packet"] + ntw.end).encode()
        
        @staticmethod
        def encode_request_players_packet() -> bytes:
            return (ntw.start + ntw.sep + ntw.types["request_players"] + ntw.sep + ntw.end).encode()
        
        @staticmethod
        def encode_pressed_trigger_packet() -> bytes:
            return (ntw.start + ntw.sep + ntw.types["pressed_trigger"] + ntw.sep + ntw.end).encode()
        
        @staticmethod
        def encode_player_eliminated_packet(username: str) -> bytes:
            return (ntw.start + ntw.sep + ntw.types["player_eliminated"] + ntw.sep + username + ntw.sep + ntw.end).encode()
        
        @staticmethod
        def encode_players_packet(usernames: list[str]) -> bytes:
            encoded_player_list = ntw.arg_list_sep.join(user for user in usernames)
            packet_data = (ntw.start + ntw.sep + ntw.types["players"] + ntw.sep + encoded_player_list + ntw.sep + ntw.end).encode()
            print(f"Sending Player Packet: {packet_data}")
            return packet_data
        
        @staticmethod
        def encode_user_disconnection() -> bytes:
            return (ntw.start + ntw.sep + ntw.types["user_disconnection"] + ntw.sep + ntw.end).encode()
        
        @staticmethod
        def encode_game_about_to_start_packet() -> bytes:
            return (ntw.start + ntw.sep + ntw.types["game_about_to_start"] + ntw.sep + ntw.end).encode()
        
        @staticmethod
        def encode_game_started_packet(number_of_chambers: int = 6) -> bytes:
            return (ntw.start + ntw.sep + ntw.types["game_started"] + ntw.sep + str(number_of_chambers) + ntw.sep + ntw.end).encode()
        
        @staticmethod
        def encode_clear_terminal_packet() -> bytes:
            return (ntw.start + ntw.sep + ntw.types["clear_terminal"] + ntw.sep + ntw.end).encode()

        
            
        
    
    class decoding:
        @staticmethod
        def decode_packet(data: bytes | str) -> tuple[str, tuple[typing.Any]]:  # type: ignore
            if type(data) == str: data = data.encode()
            
            parts = data.decode().split(ntw.sep)  # type: ignore
            
            ## start,sep,part,sep,end
            
            ############# Malformed Packet Checks #############
            if len(parts) < 3 or parts[0] != ntw.start:
                return (ntw.types["invalid_packet"], (None))  # type: ignore
            
            if parts[len(parts) - 1] != ntw.end:
                return (ntw.types["invalid_packet"], (None))  # type: ignore
            
            
            ###################################################
            
            
            if len(parts) < 2:
                return (ntw.types["invalid_packet"], (None)) # type: ignore
            
            packet_type_raw = parts[1]
            if packet_type_raw.endswith(ntw.end):
                packet_type = packet_type_raw[:-len(ntw.end)]
            else:
                packet_type = packet_type_raw
            
            if packet_type == ntw.types["heartbeat_response"]:
                return (packet_type, (ntw.decoding._decode_heartbeat_response_packet(data))) # type: ignore
            
            if packet_type == ntw.types["heartbeat"]:
                return (packet_type, (ntw.decoding._decode_heartbeat_packet(data))) # type: ignore
    
            elif packet_type == ntw.types["connection"]:
                return (packet_type, (ntw.decoding._decode_connection_packet(data)))# type: ignore
            
            elif packet_type == ntw.types["readiness"]:
                return (packet_type, (ntw.decoding._decode_readiness_packet(data)))# type: ignore
            
            elif packet_type == ntw.types["invalid_packet"]:
                return (packet_type, (ntw.decoding._decode_invalid_packet(data)))# type: ignore
            
            elif packet_type == ntw.types["request_players"]:
                return (packet_type, (ntw.decoding._decode_request_players_packet(data)))# type: ignore
            
            elif packet_type == ntw.types["game_started"]:
                return (packet_type, (ntw.decoding._decode_game_started_packet(data)))# type: ignore
            
            elif packet_type == ntw.types["pressed_trigger"]:
                return (packet_type, (ntw.decoding._decode_pressed_trigger_packet(data)))# type: ignore
            
            elif packet_type == ntw.types["player_eliminated"]:
                return (packet_type, (ntw.decoding._decode_player_eliminated_packet(data)))# type: ignore
            
            elif packet_type == ntw.types["players"]:
                return (packet_type, (ntw.decoding._decode_players_packet(data),)) # type: ignore
            
            elif packet_type == ntw.types["user_disconnection"]: 
                return (packet_type, (1,)) 
            
            elif packet_type == ntw.types["message_to_print"]:
                return (packet_type, (ntw.decoding._decode_message_to_print_packet(data)))# type: ignore
            
            elif packet_type == ntw.types["player_selected"]:
                return (packet_type, (ntw.decoding._decode_player_selected_packet(data)))# type: ignore
            
            elif packet_type == ntw.types["game_about_to_start"]:
                return (packet_type, ntw.decoding._decode_game_about_to_start_packet(data)) # type: ignore
            
            elif packet_type == ntw.types["clear_terminal"]:
                return (packet_type, ntw.decoding._decode_clear_terminal_packet(data)) # type: ignore
            
        
        @staticmethod
        def seperate_parts(packet: bytes): # type: ignore
            parts = packet.decode().split(ntw.sep)
            return parts
        
        @staticmethod
        def is_valid_packet(parts: list[str], normal_amount_of_parts: int):
            amount_of_parts = len(parts)
            try:
                packet_type = parts[2]
            except:
                if cfg.should_crash:
                    raise ntw.InvalidPacket("Failed to get type of packet (parts[2])", "reason_of_error", ntw.get_current_line_for_errors()) # Invalid Packet exception at {self.location}: (Packet Type: {self.packet_type}) {self.message}
                else:
                    return False
            
            if amount_of_parts < 3:
                if cfg.should_crash:
                    raise ntw.InvalidPacket("Packet check failed, reason is: 'amount_of_parts < 3'", packet_type, ntw.get_current_line_for_errors())
                else:
                    return False
            
            if amount_of_parts != normal_amount_of_parts:
                if cfg.should_crash:
                    raise ntw.InvalidPacket("Packet check failed, reason is: 'amount_of_parts != normal_amount_of_parts'", packet_type, ntw.get_current_line_for_errors())
                else:
                    return False
            
            return True
                
                

            
        
        
        
        
        @staticmethod
        def _decode_clear_terminal_packet(data: bytes):
            parts = ntw.decoding.seperate_parts(data)
            if len(parts) != 3 or parts[1] != ntw.types["clear_terminal"]:
                print("Decoding Error: Malformed clear terminal packet")
                return False
            return True
            
        @staticmethod
        def _decode_message_to_print_packet(data: bytes) -> bool | str: # type: ignore
            parts = ntw.decoding.seperate_parts(data)
            if len(parts) != 4 or parts[1] != ntw.types["message_to_print"]:
                print("Decoding Error: Malformed msg to print packet")
                return False
            return parts[2]
            
            
        
        @staticmethod
        def _decode_player_selected_packet(data: bytes) -> str | bool:# type: ignore
            parts = ntw.decoding.seperate_parts(data)
            if len(parts) != 4 or parts[1] != ntw.types["player_selected"]:
                print("Decoding Error: Malformed player selected packet")
                return False
            return parts[2]
        
        @staticmethod
        def _decode_heartbeat_packet(data: bytes) -> bool:
            parts = ntw.decoding.seperate_parts(data)
            if len(parts) != 3 or parts[1] != ntw.types["heartbeat"]:
                print("Decoding Error: Malformed heartbeat packet")
                return False
            return True
        
        @staticmethod
        def _decode_heartbeat_response_packet(data: bytes):
            parts = ntw.decoding.seperate_parts(data)
            if len(parts) != 4 or parts[1] != ntw.types["heartbeat_response"]:
                print("Decoding Error: Malformed hjeartbeat response packet")
                return 0
            
            try:
                player_count = int(parts[2])
            except:
                return -1
            
            return player_count
        
        @staticmethod
        def _decode_connection_packet(data: bytes) -> str | int:
            parts = ntw.decoding.seperate_parts(data)
            if len(parts) != 4 or parts[1] != ntw.types["connection"]:
                print("Decoding Error: Malformed connection packet")
                return 0
            
            return parts[2]
        
    
        @staticmethod
        def _decode_readiness_packet(data: bytes) -> bool | int:
            parts = ntw.decoding.seperate_parts(data)
            if len(parts) != 4 or parts[1] != ntw.types["readiness"]:
                print("Invalid Packet for Readiness")
                return 0

            if parts[2] == "1":
                return True
            elif parts[2] == "0":
                return False
            else:
                return None # type: ignore
            
        @staticmethod
        def _decode_invalid_packet(data: bytes) -> bool | int:
            parts = ntw.decoding.seperate_parts(data)
            if len(parts) < 2:
                return 0
            candidate = parts[1]
            if candidate.endswith(ntw.end):
                candidate = candidate[:-len(ntw.end)]
            elif len(parts) >= 3 and parts[2] == ntw.end:
                pass
            else:
                pass
            if candidate != ntw.types["invalid_packet"]:
                return 0
            return True
        
        @staticmethod
        def _decode_request_players_packet(data: bytes) -> bool | int:
            parts = ntw.decoding.seperate_parts(data)
            if len(parts) != 3:
                print("Unexpected Amount of Parts")
                return 0
            candidate = parts[1]
            if candidate != ntw.types["request_players"]:
                print("Malformed request players packet 1")
                return 0
            if not parts[2].endswith(ntw.end):
                print("Malformed request players packet 2")
                return 0
            return True
        
        @staticmethod
        def _decode_players_packet(data: bytes) -> list[str] | int:
            parts = ntw.decoding.seperate_parts(data)
            if len(parts) < 3 or parts[1] != ntw.types["players"]:
                print("Decoding Error: Malformed players packet")
                return 0
        
            # encoded_player_list = ntw.arg_list_sep.join(user for user in usernames)
            # packet_data = (ntw.start + ntw.sep + ntw.types["players"] + ntw.sep + encoded_player_list + ntw.sep + ntw.end).encode()
            # print(f"Sending Player Packet: {packet_data}")
            # return packet_data
            
            # raw_player_list = parts[]
            players = parts[2].split(ntw.arg_list_sep)
            return players
        
        @staticmethod
        def _decode_game_started_packet(data: bytes) -> bool | int:
            parts = ntw.decoding.seperate_parts(data)
            if len(parts) < 2:
                print("Decoding Error: Too little ")
                return 0
            
            candidate = parts[1]
            if candidate.endswith(ntw.end):
                candidate = candidate[:-len(ntw.end)]
            elif len(parts) >= 3 and parts[2] == ntw.end:
                pass
            else:
                pass
            if candidate != ntw.types["game_started"]:
                return 0
            return True
        
        @staticmethod
        def _decode_pressed_trigger_packet(data: bytes) -> bool | int:
            parts = ntw.decoding.seperate_parts(data)
            if len(parts) < 2:
                print("Decoding Error: Malformed Pressed Trigger packet")
                return 0
            candidate = parts[1]
            if candidate.endswith(ntw.end):
                candidate = candidate[:-len(ntw.end)]
            elif len(parts) >= 3 and parts[2] == ntw.end:
                pass
            else:
                pass
            if candidate != ntw.types["pressed_trigger"]:
                return 0
            return True
        
        @staticmethod
        def _decode_player_eliminated_packet(data: bytes) -> str | int:
            parts = ntw.decoding.seperate_parts(data)
            if len(parts) != 3 or parts[1] != ntw.types["player_eliminated"]:
                print("Decoding Error: Malformed Player Eliminated packet")
                return 0
            
            return parts[2]

        @staticmethod
        def _decode_game_about_to_start_packet(data: bytes) -> bool:
            parts = ntw.decoding.seperate_parts(data)
            if len(parts) != 3 or parts[1] != ntw.types["game_about_to_start"]:
                print("Decoding Error: Malformed Game About To Start packet")
                return False
            return True
    
        
