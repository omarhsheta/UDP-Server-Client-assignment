"""Client
   By Omar Sheta (osh18)
   ID: 92217035
   """
import socket
import select
import sys

def err(cause):
    """
    Is called when something goes wrong
    :param cause: The error message that explains what went wrong
    :return: None
    """
    print(f"ERROR: {cause}")


def checkinput(request_type, address, port_num):
    """
    This function checks the clien's request
    :param request_type: Has to be either 'date' or 'time'
    :param address: Checks IP address
    :param port_num: checks if the client has inputted the right port number or not
    :return: None
    """
    if request_type.lower() not in ['date', 'time']:
        err("Invalid request, closing the client")
        sys.exit()
    else:
        try:
            converted = socket.gethostbyname(address)
        except socket.error:
            err("Invalid address, closing the client")
            sys.exit()
        try:
            port_num = int(port_num)
            if port_num <= 1024 or port_num >= 64000:
                err("Incorrect port number value, closing the client")
                sys.exit()
        except:
            err("Invalid port number, closing the client")
            sys.exit()
    print("CLIENT: Input check has passed!")


def dt_request(magicNum, packetType, requestType):
    """
    Builds a request packet
    :param magicNum: Always has to be 0x497E
    :param packetType: Always has to be 0x0001
    :param requestType: Can either be 0x0001 or 0x0002, indicating Date or time respectively
    :return: the request packet
    """
    result = bytearray()
    result += magicNum.to_bytes(2, byteorder='big') + packetType.to_bytes(2, byteorder='big') + requestType.to_bytes(2, byteorder='big')
    return result


def check_response(packet):
    """
    Checks if the dt_response packet is not corrupt
    :param packet: dt_response packet
    :return: the relevant data from the packet
    """
    print("CLIENT: Checking the received packet...")
    if len(packet) < 13:
        err("Packet too short, closing the client...")
        sys.exit()
    else:
        data = packet[13:]
        if int.from_bytes(packet[:2], byteorder='big') != 0x497E:
            err("The magic number is incorrect, closing the client...")
            sys.exit()
        elif int.from_bytes(packet[2:4], byteorder='big') != 0x002:
            err("Wrong packet type, closing the client...")
            sys.exit()
        elif int.from_bytes(packet[4:6], byteorder='big') not in [0x0001, 0x0002, 0x0003]:
            err("Invalid language code, closing the client...")
            sys.exit()
        elif int.from_bytes(packet[6:8], byteorder='big') >= 2100:
            err("Invalid year, closing the client...")
            sys.exit()
        elif packet[8] not in list(range(1, 13)):
            err("Invalid month number, closing the client...")
            sys.exit()
        elif packet[9] not in list(range(1, 32)):
            err("Invalid day number, closing the client...")
            sys.exit()
        elif packet[10] not in list(range(0, 24)):
            err("Invalid hour, closing the client...")
            sys.exit()
        elif packet[11] not in list(range(0, 60)):
            err("Invalid minute, closing the client...")
            sys.exit()
        elif len(packet) != (13 + len(data)):
            err("Inconsistent packet length, closing the client...")
            sys.exit()
        else:
            print("CLIENT: Packet check passed!")
            print("CLIENT: Printing header content\n\n")
            #prints the contents of the packet's header
            print("Byte form | Numerical value\n"
                  f"{int.from_bytes(packet[:2], byteorder='big'):#0{6}x}    | {int.from_bytes(packet[:2], byteorder='big')}\n"
                  f"{int.from_bytes(packet[2:4], byteorder='big'):#0{6}x}    | {int.from_bytes(packet[2:4], byteorder='big')}\n"
                  f"{int.from_bytes(packet[4:6], byteorder='big'):#0{6}x}    | {int.from_bytes(packet[4:6], byteorder='big')}\n"
                  f"{int.from_bytes(packet[6:8], byteorder='big'):#0{6}x}    | {int.from_bytes(packet[6:8], byteorder='big')}\n"
                  f"{packet[8]:#0{6}x}    | {packet[8]}\n"
                  f"{packet[9]:#0{6}x}    | {packet[9]}\n"
                  f"{packet[10]:#0{6}x}    | {packet[10]}\n"
                  f"{packet[11]:#0{6}x}    | {packet[11]}\n\n"
                  )
            return data


def print_message(data):
    """
    Prints out the message from dt_response packet
    :param data: the data of the packet in bytes
    :return: None
    """
    #
    #Make sure to print the bytes accordingly
    #
    print("\n"+data.decode("utf-8"))


def main():
    try:
        request_type, ip_num, port_num = input("Please enter the request (date or time), the IP Address of the server, "
                                               "and the port number: ").split()
        print("CLIENT: Checking input...")
        checkinput(request_type, ip_num, port_num)
        s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM, proto=0, fileno=None)
        if request_type.lower() == 'date':
            packet = dt_request(0x497E, 0x0001, 0x0001)
        else:
            packet = dt_request(0x497E, 0x0001, 0x0002)
        print("CLIENT: Sending the packet...")
        try:
            s.sendto(packet, (ip_num, int(port_num)))
        except OSError:
            err("The client could not reach the address, closing the client")
            sys.exit()
        print("CLIENT: Waiting for response...")
        response, _, _ = select.select([s], [], [], 1.0)
        if len(response) == 0:
            err("Nothing received, closing the client")
            sys.exit()
        try:
            data, addr = s.recvfrom(4096)
            text = check_response(data)
            print_message(text)
            s.close()
            sys.exit()
        except ConnectionResetError:
            err("Could not connect to the Server, closing the client")
    except ValueError:
        err("Couldn't read the input, closing the client")

main()