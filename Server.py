"""Server
   By Omar Sheta (osh18)
   ID: 92217035
   """
from datetime import datetime
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


def check_portnums(eng, mao, ger):
    """
    Checks if the port numbers are not identical and have correct values
    :param eng: English port number
    :param mao: Te Reo Maori port number
    :param ger: German port number
    :return:
    """
    print("SERVER: Checking port numbers")
    if eng == mao or eng == ger or mao == ger:
        err("Two or more identical port numbers, closing the server...")
        sys.exit()
    elif eng <= 1024 or eng >= 64000:
        err("English Port Number has incorrect value, closing the server...")
        sys.exit()
    elif mao <= 1024 or mao >= 64000:
        err("Te Reo Maori Port Number has incorrect value, closing the server...")
        sys.exit()
    elif ger <= 1024 or ger >= 64000:
        err("German Port Number has incorrect value, closing the server...")
        sys.exit()
    else:
        print("SERVER: Port numbers check has passed!")


def create_socket(port_num, lang):
    """
    Creates a UDP/Datagram socket, and then binds it with the port number
    :param port_num: Any integer from 1024 to 64000 (Exclusive)
    :param lang: string that should be either 'eng', 'mao', or 'ger' for English, Te Reo Maori, and German respectively
    :return: returns a tuple with the socket and the index of the languages. The latter will be used
             for packet processing later on
    """
    print(f"SERVER: Creating UDP socket for {lang} date/time requests...")
    lang_num = ['eng', 'mao', 'ger']
    s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM, proto=0, fileno=None)
    try:
        print(f"SERVER: Binding the {lang} socket with the port number {port_num}...")
        s.bind(("0.0.0.0", port_num))
    except socket.error:
        err(f"The port number {port_num} could not be bound to the {lang} socket, closing the server...")
        sys.exit()
    try:
        language_ind = lang_num.index(lang)
    except ValueError:
        err("The specified language is either not available or incorrectly spelt, closing the server...")
        sys.exit()
    print(f"SERVER: UDP socket for {lang} has been successfully created!")
    return s, language_ind


def text(d_type, lang, date, time):
    """
    :param d_type: decides the type of text to be returned, if it is 0x0001 then it will return the current date,
                   if it is 0x0002, then it will return the current time. Otherwise, the function will return None.
    :param lang: has to be either 0, 1, 2; otherwise returns None
    :param date: Can either be None or have a tuple of three values containing 'year', 'month', and 'day'; however,
                 it cannot be the same as time or it will return None
    :param time: Can either be None or have a tuple of two values containing 'hour' and 'minutes'; however,
                 it cannot be the same as date or it will return None
    :return: Returns None if something is wrong with the parameters, or returns an encoded message in bytes.
    """
    if d_type not in [0x0001, 0x0002] or lang not in [0, 1, 2]:
        return None
    else:
        if d_type == 0x0001:
            eng_months = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
                          "October",
                          "November", "December"]
            mao_months = ["Kohi-tātea", "Hui-tanguru", "Poutū-te-rangi", "Paenga-whāwhā", "Haratua", "Pipiri",
                          "Hōngongoi", "Here-turi-kōkā", "Mahuru", "Whiringa-ā-nuku", "Whiringa-ā-rangi", "Hakihea"]
            ger_months = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober",
                          "November", "Dezember"]
            months = [eng_months, mao_months, ger_months]
            year, month, day = date
            text = [f"Today's date is {months[lang][month - 1]} {day}, {year}",
                    f"Ko te ra o tenei ra ko {months[lang][month - 1]} {day}, {year}",
                    f"Huete ist der {day}. {months[lang][month - 1]} {year}"]
            return text[lang].encode('utf-8')
        elif d_type == 0x0002:
            hour, minute = time
            if minute < 10:
                text = [f"The current time is {hour}:0{minute}",
                        f"Ko te wa o tenei wa {hour}:0{minute}",
                        f"Die Uhrzeit ist {hour}:0{minute}"]
                return text[lang].encode('utf-8')
            else:
                text = [f"The current time is {hour}:{minute}",
                        f"Ko te wa o tenei wa {hour}:{minute}",
                        f"Die Uhrzeit ist {hour}:{minute}"]
                return text[lang].encode('utf-8')


def dt_response(magicNum, languageCode, year, month, day, hour, minute, length, text):
    """
    Sets a packet in a form of bytearray
    :param magicNum: 0x497E
    :param languageCode: 0x0001 for English, 0x0002 for Te Reo Maori, and 0x0003 for German
    :param year: it is the current year
    :param month: it is the current month
    :param day: it is the current day
    :param hour: it is the current hour
    :param minute: it is the current minute
    :param length: length of the text
    :param text: the content of the message to be sent to the client
    :return: a packet in a form of bytearray type
    """
    packet = bytearray()
    packet += magicNum
    packet += (2).to_bytes(2, byteorder='big')
    packet += languageCode.to_bytes(2, byteorder='big')
    packet += year.to_bytes(2, byteorder='big')
    packet += month.to_bytes(1, byteorder='big')
    packet += day.to_bytes(1, byteorder='big')
    packet += hour.to_bytes(1, byteorder='big')
    packet += minute.to_bytes(1, byteorder='big')
    packet += length.to_bytes(1, byteorder='big')
    packet += text
    return packet


def response_to_client(sock, addr, data, lang_num):
    """
    Prepares to send a response to the client
    :param sock: the used socket
    :param addr: the IP address of the client
    :param data: the request information from the client
    :param lang_num: the index of the language to be used
    :return: None
    """
    if len(data) != 6:
        err("Improper data length, discarding the packet")
    elif int.from_bytes(data[:2], byteorder='big') != 0x497E:
        err("Incorrect MagicNum, discarding the packet")
    elif int.from_bytes(data[2:4], byteorder='big') != 0x0001:
        err("Incompatible PacketType, discarding the packet")
    elif int.from_bytes(data[4:], byteorder='big') not in [0x0001, 0x0002]:
        err("Unknown request, discarding the packet")
    else:
        print("SERVER: Processing the request, please wait.")
        date = str(datetime.date(datetime.now()))
        year = int(date[:4])
        month = int(date[5:7])
        day = int(date[8:])
        time = str(datetime.time(datetime.now()))
        hour = int(time[:2])
        minute = int(time[3:5])
        textual = text(int.from_bytes(data[4:], byteorder='big'), lang_num, (year, month, day), (hour, minute))
        if textual is None:
            err("Invalid message! Discarding the request.")
        else:
            len_text = len(textual)
            if len_text > 255:
                err("Message is too long! Discarding the request.")
            else:
                packet = dt_response(data[:2], (lang_num + 1), year, month, day, hour, minute, len_text, textual)
                sock.sendto(packet, addr)
                print("SERVER: Response sent, now listening to more responses!\n")


def main():
    """
    The function that runs everything
    """
    try:
        eng, mao, ger = input("Please input three 'different' port numbers separated by whitespaces\n"
                              "First for English, Second for Te Reo Maori, and third for German: ").split()
        check_portnums(int(eng), int(mao), int(ger))
    except ValueError:
        err("Invalid input, closing the server...")
        sys.exit()
    eng_socket = create_socket(int(eng), "eng")
    mao_socket = create_socket(int(mao), "mao")
    ger_socket = create_socket(int(ger), "ger")
    lang_nums = [eng_socket[1], mao_socket[1], ger_socket[1]]
    sockets = [eng_socket[0], mao_socket[0], ger_socket[0]]
    while True:
        print("SERVER: Waiting for a connection...")
        response, _, _ = select.select(sockets, [], [])
        sock_ind = sockets.index(response[0])
        lang_num = lang_nums[sock_ind]
        languages = ["English", "Te Reo Maori", "German"]
        print("SERVER: A client has connected!")
        print("SERVER: Receiving a request...")
        rec_packet, addr = response[0].recvfrom(4096)
        print(f"SERVER: Request received from {addr[0]} in {languages[lang_num]}!")
        byte_data = bytearray()
        byte_data += rec_packet
        response_to_client(response[0], addr, byte_data, lang_num)


main()
