import os
import queue
import typing
import inspect
import logging
import datetime

class cfg:
    should_crash = True
    
    
##################################################### Logging Window ('borrowed' from stackoverflow) #####################################################
try:
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
except:
    print("Failed to initalize ui, continuing without ui...")
        
        


            
            
#####################################################################################################################################################



class ntw:
    default_port = 2046
    default_host = "localhost"
    
    start = "(*"
    sep = "|||"
    end = "*)"
    max_packet_size = 512
    arg_list_sep = "|l|"
    
    @staticmethod
    def validate_username(username: str) -> tuple:
        if len(username) > 20: # If the username is larger that 20 characters
            return False, "Your username shouldn't be larger than 20 characters", 0.04
        
        if "," in username:
            return False, "As you should have read above, no commas (,) are allowed in your username", 0.04
        
        if username.isnumeric():
            return False, "Your username shouldn't only consist of numbers so other players can tell it's a real name and not just random numbers", 0.03
        
        if "*)" in username or "(*" in username or "|" in username or "[" in username or "]" in username:
            return False, "For top secret reasons, your username cant contain the following: (*  *)  ,   |  [  ]", 0.04
        
        return True, "", 0.06
    
    class packets:
        class general_packet:
            RAW: str
            ARG_NUMBER: int
            SIDE: typing.Literal["client", "server", "both"]
            
        class heartbeat(general_packet):
            RAW = "hbt"
            ARG_NUMBER = 0
            SIDE = "client"
            @classmethod
            def encode(cls):
                return (ntw.start + ntw.sep + cls.RAW + ntw.sep + ntw.end).encode()
        class heartbeat_response(general_packet):
            RAW = "hbt_rsp"
            ARG_NUMBER = 1
            SIDE = "server"
            @classmethod
            def encode(cls, player_count):
                return (ntw.start + ntw.sep + cls.RAW + ntw.sep + str(player_count) + ntw.sep + ntw.end).encode()      
        class connection(general_packet):
            RAW = "con"
            ARG_NUMBER = 1
            SIDE = "client"
            @classmethod
            def encode(cls, username: str) -> bytes:
                return (ntw.start + ntw.sep + cls.RAW + ntw.sep + str(username) + ntw.sep + ntw.end).encode()
        class readiness(general_packet):
            RAW = "rdy"
            ARG_NUMBER = 1
            SIDE = "client"
            @classmethod
            def encode(cls, ready: bool) -> bytes:
                ready_state = "1" if ready else "0"
                return (ntw.start + ntw.sep + cls.RAW + ntw.sep + ready_state + ntw.sep + ntw.end).encode()
        class invalid_packet(general_packet):
            RAW = "error_pckt"
            ARG_NUMBER = 0
            SIDE = "both"
            @classmethod
            def encode(cls):
                return (ntw.start + ntw.sep + cls.RAW + ntw.sep + ntw.end).encode()
        class request_players(general_packet):
            RAW = "rq_plys"
            ARG_NUMBER = 0
            SIDE = "client"
            @classmethod
            def encode(cls):
                return (ntw.start + ntw.sep + cls.RAW + ntw.sep + ntw.end).encode()
        class players(general_packet):
            RAW = "plrs"
            ARG_NUMBER = 1
            SIDE = "server"
            @classmethod
            def encode(cls, usernames: list[str]) -> bytes:
                encoded_player_list = ntw.arg_list_sep.join(user for user in usernames)
                return (ntw.start + ntw.sep + cls.RAW + ntw.sep + str(encoded_player_list) + ntw.sep + ntw.end).encode()
        class game_started(general_packet):
            RAW = "g_start"
            ARG_NUMBER = 0
            SIDE = "server"
            @classmethod
            def encode(cls):
                return (ntw.start + ntw.sep + cls.RAW + ntw.sep + ntw.end).encode()
        class game_about_to_start(general_packet):
            RAW = "abt_start"
            ARG_NUMBER = 0
            SIDE = "server"
            @classmethod
            def encode(cls):
                return (ntw.start + ntw.sep + cls.RAW + ntw.sep + ntw.end).encode()
        class pressed_trigger(general_packet):
            RAW = "trig"
            ARG_NUMBER = 0
            SIDE = "client"
            @classmethod
            def encode(cls):
                return (ntw.start + ntw.sep + cls.RAW + ntw.sep + ntw.end).encode()
        class player_eliminated(general_packet):
            RAW = "ply_elim"
            ARG_NUMBER = 1
            SIDE = "server"
            @classmethod
            def encode(cls, username: str) -> bytes:
                return (ntw.start + ntw.sep + cls.RAW + ntw.sep + str(username) + ntw.sep + ntw.end).encode()
        class user_disconnection(general_packet):
            RAW = "ply_dis"
            ARG_NUMBER = 0
            SIDE = "client"
            @classmethod
            def encode(cls):
                return (ntw.start + ntw.sep + cls.RAW + ntw.sep + ntw.end).encode()
        class message_to_print(general_packet):
            RAW = "msg"
            ARG_NUMBER = 1
            SIDE = "server"
            @classmethod
            def encode(cls, message: str) -> bytes:
                return (ntw.start + ntw.sep + cls.RAW + ntw.sep + str(message) + ntw.sep + ntw.end).encode()
        class player_selected(general_packet):
            RAW = "ply_sel"
            ARG_NUMBER = 1
            SIDE = "server"
            @classmethod
            def encode(cls, player_selected: str) -> bytes:
                return (ntw.start + ntw.sep + cls.RAW + ntw.sep + str(player_selected) + ntw.sep + ntw.end).encode()
        class clear_terminal(general_packet):
            RAW = "cls_term"
            ARG_NUMBER = 0
            SIDE = "server"
            @classmethod
            def encode(cls):
                return (ntw.start + ntw.sep + cls.RAW + ntw.sep + ntw.end).encode()
        class invalid_username(general_packet):
            RAW = "inv_usrname"
            ARG_NUMBER = 1
            SIDE = "server"
            @classmethod
            def encode(cls, msg: str, delay: float = 0.06):
                return (ntw.start + ntw.sep + cls.RAW + ntw.sep + str(msg) + ntw.sep + str(delay) + ntw.sep + ntw.end).encode()
    
    @classmethod
    def get_packet_by_raw(cls, raw: str):
        for name, cls in ntw.packets.__dict__.items():
            if isinstance(cls, type) and hasattr(cls, "RAW") and cls.RAW == raw:
                return cls
        return None

    
    class InvalidPacket(Exception):
        """Exception raised when a packet is invalid and unable to be decoded/encoded"""
        def __init__(self, message, packet_type: str, location: str):
            super().__init__(message)
            self.message = message
            self.packet_type = packet_type
            self.location = location

        def __str__(self):
            return f"Invalid Packet exception at '{self.location}': (Packet Type: {self.packet_type}): {self.message}"  # type: ignore
        
    @staticmethod
    def get_current_line_for_errors() -> str:
        frame = inspect.currentframe().f_back # type: ignore
        file_name = os.path.basename(frame.f_code.co_filename) # type: ignore
        func_name = frame.f_code.co_name # type: ignore
        line_number = frame.f_lineno # type: ignore
        return f"Line {line_number}, Function {func_name}, File {file_name}" 
        
            
        
    
    class decoding:
        @staticmethod
        def decode_packet(data: bytes | str) -> tuple: # type: ignore
            """
            If packet is valid, returns: (packet_type: str, packet_class: ntw.general_packet, parts: list)
            
            If packet is invalid (and config is set to crash, default): raises ntw.InvalidPacket
            If packet is invalid (and config is set to not crash), returns (ntw.packets.invalid_packet.RAW, packet_class: object, error_msg: str)
            """
            if type(data) == str: data = data.encode()
            
            parts = ntw.decoding.seperate_parts(data) # type: ignore

            ############# Malformed Packet Checks #############

            raw_packet_type = parts[1]
            packet_class = ntw.get_packet_by_raw(raw_packet_type) # returns the class of the packet
            
            normal_amount_of_parts = 3 + packet_class.ARG_NUMBER #type: ignore
            if not ntw.decoding.is_valid_packet(parts, normal_amount_of_parts):
                if cfg.should_crash:
                    raise ntw.InvalidPacket(f"Decoding Error: is_valid_packet returned false", raw_packet_type, ntw.get_current_line_for_errors())
                else:
                    return (ntw.packets.invalid_packet.RAW, packet_class,f"Decoding Error: is_valid_packet returned false at {ntw.get_current_line_for_errors()}")

            if packet_class == None:
                if cfg.should_crash:
                    raise ntw.InvalidPacket("Decoding Error: possible_packet_type is None", raw_packet_type, ntw.get_current_line_for_errors())
                else:
                    return (ntw.packets.invalid_packet.RAW, packet_class, f"Decoding Error: possible_packet_type is None at {ntw.get_current_line_for_errors()}")
            
            if packet_class.ARG_NUMBER == 0:
                return (raw_packet_type, packet_class, None)
            
            if packet_class.ARG_NUMBER > 0:
                args = parts
                args.remove(ntw.start) 
                args.remove(raw_packet_type)
                args.remove(ntw.end)
                return (raw_packet_type, packet_class, parts)
            
        
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