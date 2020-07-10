import socket
import pprint
import json

STATUS = 1
LOGIN = 2


def encode_varint(i):
    if i==0: return b'\x00'
    b=[]
    while i:
        b.append((i & 0x7f) | 0x80)
        i >>= 7
    b[-1] &= 0x7f
    return bytes(b)

def decode_varint(b):
    result=0
    for i, c in enumerate(b):
        result |= ((c & 0x7f) << (i*7))
        if not (c & 0x80):
            return result, b[i+1:]
    return result, None


def encode_string(s):
    b=s.encode('utf8')
    return encode_varint(len(b))+b


def encode_packet_uncompressed(packet_id, packet):
    # For SOME reason, the length field of packets going TO the server does NOT include the length of the packet ID,
    # but the length field of packets coming FROM the server does
    return encode_varint(len(packet))+encode_varint(packet_id)+packet


NEGATIVE_ONE = 4294967295


def receive_packet_uncompressed(sock):
    sock.settimeout(5)
    data=sock.recv(16)
    packet_length, data = decode_varint(data)
    packet_id, _ = decode_varint(data)
    while len(data) < packet_length:
        try:
            new_data = sock.recv(packet_length - len(data))
        except socket.timeout:
            raise ValueError(f'Received packet was {packet_length-len(data)} bytes too short')
        data += new_data
    return packet_id, data[1:]


def handshake(host, port=25565, next_action = LOGIN):
    s = socket.create_connection((host, port))

    # Anatomy of a handshake packet (Python won't let me put my comments mid-line):
    # NEGATIVE_ONE = the protocol version.  -1 should be used if we are pinging to determine
    # what protocol version to use, which we are.  The constant NEGATIVE_ONE defined at the top of the file
    # in fact has a value of 2^32-1, which is because the Minecraft server, being written in Java,
    # rather naively treats varints as 32-bit signed integers.  Python, on the other hand, as you know,
    # treats integers as infinitely wide, so if we passed an actual negative number to encode_varint(), it would
    # iterate until it ran out of memory.
    # Second filed is the hostname.  Forge servers will immediately drop the connection unless you tack
    # '\x00FML\x00' onto the hostname -- vanilla servers ignore it.
    # (It stands for Forge Mod Loader although I think we all know it really stands
    # for someting else -- really?  straight up the connection after ONE protocol violation?  Not even an error
    # message!?)
    # Last two fields are self explanatory.

    handshake_packet = \
        encode_varint(NEGATIVE_ONE) + \
        encode_string(host+'\0FML\0') + \
        encode_varint(port) + \
        encode_varint(next_action)

    # packet ID 0 = handshake
    s.sendall(encode_packet_uncompressed(0, handshake_packet))
    return s


def server_list_ping(host, port=25565):
    s=handshake(host, port, STATUS) # 1 for status, 2 for actually logging into the server.
    s.sendall(encode_packet_uncompressed(0, b''))  # packet ID 0 in Status state = server info.
    response_packetid, response = receive_packet_uncompressed(s)
    assert response_packetid == 0, f'Server responded with packet ID %d' % response_packetid
    length_of_json, response = decode_varint(response)
    assert length_of_json == len(response)
    respj = json.loads(response.decode('utf8'))
    pprint.pprint(respj)
    if 'forgeData' in respj:
        print('1.13 or later')
        mods={m['modId']: m['modmarker'] for m in respj['forgeData']['mods']}
    elif 'modinfo' in respj:
        print('1.12.2 or earlier')
        print('modloader:', respj['modinfo']['type'])
        mods = {m['modid']: m['version'] for m in respj['modinfo']['modList']}
    else:
        print('Vanilla', respj['version']['name'])
        mods={}
    print(mods)


def legacy_encode(b):
    return len(b).to_bytes(2, 'big')+b

def legacy_ping(host, port=25565):
    """Legacy server list ping, from 1.4 to 1.6"""
    s=socket.create_connection((host, port))
    s.sendall(b'\xfe\x01\xfa') # ping packet (0xFE), payload (0x01), and packet ID (0xFA for a plugin message)
    s.sendall(legacy_encode('MC|PingHost'.encode('utf-16-be')))  # the plugin we want to talk to.
    s.sendall(legacy_encode(b'\74' + # 74 is the last protocol version used by 1.6 and earlier
                            legacy_encode(host.encode('utf-16-be')) +
                            port.to_bytes(4, 'big')
    ))
    s.shutdown(socket.SHUT_WR)  # not strictly necessary but a good idea.
    resp=s.recv(3)
    assert resp[0] == 0xFF  # 0xFF = kick packet
    length=int.from_bytes(resp[1:], 'little') * 2  # length field is the number of characters, double it for utf16 bytes
    print(length)
    proto_ver, game_ver, motd, players, max_players = s.recv(length).decode('utf-16-be').split('\0')
    players = int(players)
    max_players = int(max_players)
    print('(%d/%d) [%s] %s' % (players, max_players,game_ver, motd))




def very_old_ping(host, port):
    """Server list ping for pre-1.4 (still works on 1.12 servers for some reason)"""
    s=socket.create_connection((host, port))
    s.sendall(b'\xfe')
    response=s.recv(3)
    assert response[0]==0xff # kick packet
    length=int.from_bytes(response[1:], 'big')*2  # length is the number of characers; utf16 uses 2 bytes per character
    motd, players, max_players = s.recv(length).decode('utf-16-be').split('§')
    players=int(players)
    max_players=int(max_players)
    print('(%d/%d) %s'%(players, max_players, motd))

if __name__=='__main__':
    server_list_ping('mcsl.nemegaming.org',25565)