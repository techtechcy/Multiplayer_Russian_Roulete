import typing
import threading
import msvcrt
import time

class ntw:
    start = "(*"
    sep = ","
    end = "*)"
    types = {
        "heartbeat": "hbt",
        "heartbeat_response": "hbt_rsp",
        "connection": "con",
        "readiness": "rdy",
        "invalid_packet": "inv",
        "request_players": "rq_ply",
        "players": "plrs",
        "game_started": "gm_strt",
        "pressed_trigger": "prs_trg",
        "player_eliminated": "ply_elim",
        "user_disconnection": "usr_dsc"
    }
    
    max_packet_size = 1024
    
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
        def encode_game_started_packet() -> bytes:
            return (ntw.start + ntw.sep + ntw.types["game_started"] + ntw.sep + ntw.end).encode()
        
        @staticmethod
        def encode_pressed_trigger_packet() -> bytes:
            return (ntw.start + ntw.sep + ntw.types["pressed_trigger"] + ntw.sep + ntw.end).encode()
        
        @staticmethod
        def encode_player_eliminated_packet(username: str) -> bytes:
            return (ntw.start + ntw.sep + ntw.types["player_eliminated"] + ntw.sep + username + ntw.sep + ntw.end).encode()
        
        @staticmethod
        def encode_players_packet(usernames: list[str]) -> bytes:
            players_str = ntw.sep.join(usernames)
            return (ntw.start + ntw.sep + ntw.types["players"] + ntw.sep + players_str + ntw.sep + ntw.end).encode()
        
        @staticmethod
        def encode_user_disconnection() -> bytes:
            return (ntw.start + ntw.sep + ntw.types["user_disconnection"] + ntw.sep + ntw.end).encode()
        

        
            
        
    
    class decoding:
        @staticmethod
        def decode_packet(data: bytes | str) -> tuple[str, tuple[typing.Any]]:
            if type(data) == str: data = data.encode()
            
            parts = data.decode().split(ntw.sep)
            
            ## start, sep,part,sep,end
            
            ############# Malformed Packet Checks #############
            if len(parts) < 3 or parts[0] != ntw.start:
                return ntw.types["invalid_packet"], (None)
            
            if parts[len(parts) - 1] != ntw.end:
                return ntw.types["invalid_packet"], (None)
            
            
            ###################################################
            
            
            if len(parts) < 2:
                return (None, None)
            
            packet_type_raw = parts[1]
            if packet_type_raw.endswith(ntw.end):
                packet_type = packet_type_raw[:-len(ntw.end)]
            else:
                packet_type = packet_type_raw
            
            if packet_type == ntw.types["heartbeat_response"]:
                return (packet_type, (ntw.decoding._decode_heartbeat_response_packet(data)))
            
            if packet_type == ntw.types["heartbeat"]:
                return (packet_type, (ntw.decoding._decode_heartbeat_packet(data)))
    
            elif packet_type == ntw.types["connection"]:
                return (packet_type, (ntw.decoding._decode_connection_packet(data)))
            
            elif packet_type == ntw.types["readiness"]:
                return (packet_type, (ntw.decoding._decode_readiness_packet(data)))
            
            elif packet_type == ntw.types["invalid_packet"]:
                return (packet_type, (ntw.decoding._decode_invalid_packet(data)))
            
            elif packet_type == ntw.types["request_players"]:
                return (packet_type, (ntw.decoding._decode_request_players_packet(data)))
            
            elif packet_type == ntw.types["game_started"]:
                return (packet_type, (ntw.decoding._decode_game_started_packet(data)))
            
            elif packet_type == ntw.types["pressed_trigger"]:
                return (packet_type, (ntw.decoding._decode_pressed_trigger_packet(data)))
            
            elif packet_type == ntw.types["player_eliminated"]:
                return (packet_type, (ntw.decoding._decode_player_eliminated_packet(data)))
            
            elif packet_type == ntw.types["players"]:
                return (packet_type, (ntw.decoding._decode_players_packet(data)))
            
            elif packet_type == ntw.types["user_disconnection"]:
                return (packet_type, 1)
            
            
            
            
            
        
        @staticmethod
        def _decode_heartbeat_packet(data: bytes) -> bool:
            parts = data.decode().split(ntw.sep)
            if len(parts) == 3 or parts[1] != ntw.types["heartbeat"]:
                return False
            return True
        
        @staticmethod
        def _decode_heartbeat_response_packet(data: bytes) -> int | int:
            parts = data.decode().split(ntw.sep)
            if len(parts) != 3 or parts[1] != ntw.types["heartbeat_response"]:
                return 0
            
            try:
                player_count = int(parts[2])
            except:
                return -1
            
            return player_count
        
        @staticmethod
        def _decode_connection_packet(data: bytes) -> str | int:
            parts = data.decode().split(ntw.sep)
            if len(parts) != 3 or parts[1] != ntw.types["connection"]:
                return 0
            
            return parts[2]
        
    
        @staticmethod
        def _decode_readiness_packet(data: bytes) -> bool | int:
            parts = data.decode().split(ntw.sep)
            if len(parts) != 4 or parts[1] != ntw.types["readiness"]:
                print("Invalid Packet for Readiness")
                return 0

            if parts[2] == "1":
                return True
            elif parts[2] == "0":
                return False
            else:
                return None
            
        @staticmethod
        def _decode_invalid_packet(data: bytes) -> bool | int:
            parts = data.decode().split(ntw.sep)
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
            parts = data.decode().split(ntw.sep)
            if len(parts) < 2:
                return 0
            candidate = parts[1]
            if candidate.endswith(ntw.end):
                candidate = candidate[:-len(ntw.end)]
            elif len(parts) >= 3 and parts[2] == ntw.end:
                pass
            else:
                pass
            if candidate != ntw.types["request_players"]:
                return 0
            return True
        
        @staticmethod
        def _decode_players_packet(data: bytes) -> list[str] | int:
            parts = data.decode().split(ntw.sep)
            if len(parts) < 3 or parts[1] != ntw.types["players"]:
                return 0
            
            players = []
            for i in range(2, len(parts)):
                candidate = parts[i]
                if candidate.endswith(ntw.end):
                    candidate = candidate[:-len(ntw.end)]
                if candidate:
                    players.append(candidate)
            
            return players
        
        @staticmethod
        def _decode_game_started_packet(data: bytes) -> bool | int:
            parts = data.decode().split(ntw.sep)
            if len(parts) < 2:
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
            parts = data.decode().split(ntw.sep)
            if len(parts) < 2:
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
            parts = data.decode().split(ntw.sep)
            if len(parts) != 3 or parts[1] != ntw.types["player_eliminated"]:
                return 0
            
            return parts[2]
        
