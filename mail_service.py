import imaplib
import email
import re
import base64
import quopri
import os
import time
import telebot
import sqlite3

attachments_dir = "//files//"
token = "1010830562:AAHeFoZaEuK7FgiP8kwDtbofuPwHgtMJDL8"
bot = telebot.TeleBot(token)
ID = -1001445233947 # "716986295"


def encoded_words_to_text(encoded_words):
    encoded_word_regex = r'=\?{1}(.+)\?{1}([b|B|Q|q])\?{1}(.+)\?{1}='
    charset, encoding, encoded_text = re.match(encoded_word_regex, encoded_words).groups()
    if encoding.upper() == 'B':
        byte_string = base64.b64decode(encoded_text)
    elif encoding.upper() == 'Q':
        byte_string = quopri.decodestring(encoded_text)
    return byte_string.decode(charset)


def decode_this_shit_suka_blyat(shit):
    truly_shit = re.search("=.+=", shit)
    if truly_shit:
        return encoded_words_to_text(truly_shit.group())
    else:
        return None


def get_body(message):
    if message.is_multipart():
        return get_body(message.get_payload(0))
    else:
        return message.get_payload(None, True).decode()


def get_message(client):
    print("Getting mail!")
    client.select("INBOX")
    result, emails = client.uid("search", None, "ALL")
    if result == "OK":  # якщо запит пройшов успішно
        last_email = emails[0].split()
        if len(last_email):
            last_email = last_email[-1]  # беремо іd останній лист

            result, email_data = client.uid("fetch", last_email, "(RFC822)")  # беремо тіло листа
            row_email_data = email_data[0][1]


            # post_box.uid("STORE", last_email, "+FLAGS", "\\Deleted")  # видаляємо останній лист
            # post_box.expunge()

            return email.message_from_bytes(row_email_data)
    return None


def get_attachments(message):
    path_array = []
    for part in message.walk():
        if part.get_content_maintype() == "multipart":
            continue
        if part.get("Content-Disposition") is None:
            continue
        file_name = part.get_filename()
        if bool(file_name):
            file_path = os.path.join(attachments_dir, get_encoded_word(file_name))
            print(file_path)
            with open(file_path, "wb") as data:
                data.write(part.get_payload(decode=True))
            path_array.append(file_path)
            print("Прикріплені файл збережений")
    return path_array


def get_encoded_word(message):
    array = message.split()
    result = ""
    for item in array:
        encoded = decode_this_shit_suka_blyat(item)
        if encoded:
            result += encoded + " "
        else:
            result += item + " "
    return result


if __name__ == "__main__":
    print("starting")
    username = "iasa-da92@ukr.net"
    password = "9rhj7QTsiCaovoAd"
    imap_url = "imap.ukr.net"

    send_report = 0

    connection = sqlite3.connect('db.sqlite3')
    cursor = connection.cursor()

    while True:
        post_box = imaplib.IMAP4_SSL(imap_url)
        post_box.login(username, password)

        try:
            email_obj = get_message(post_box)

            send_report += 1
            if send_report == 180:
                bot.send_message(716986295, "Працює найс.")
                send_report = 0

            if email_obj:
                receiver = email_obj["To"]
                sender = email_obj["From"]
                subject = email_obj["Subject"]

                body = get_body(email_obj)

                paths = get_attachments(email_obj)

                receiver = "Кому: " + get_encoded_word(receiver) + "\n"
                sender = "Хто: " + get_encoded_word(sender) + "\n"
                subject = "Заголовок: " + get_encoded_word(subject) + "\n"
                letter = receiver + sender + subject + body

                """with open('last_letter.txt', 'r') as f:
                    last_letter = f.read()"""
                cursor.execute('SELECT last FROM Mail')
                last_letter = cursor.fetchone()[0]

                if letter.split() != last_letter.split():

                    """with open('last_letter.txt', 'w') as f:
                        f.write(letter)"""

                    cursor.execute('UPDATE Mail SET last=?', (letter,))
                    connection.commit()

                    print("пересилаю...")
                    if len(letter) > 4096:
                        print("Big mail")
                        i = 0
                        j = 1
                        while i < len(letter):
                            print("part", j)
                            if len(letter[i:]) < 4096:
                                bot.send_message(ID, letter[i:])
                                break
                            bot.send_message(ID, letter[i:i + 4096])
                            i += 4096
                            j += 1
                    else:
                        bot.send_message(ID, letter)

                    if len(paths):
                        for path in paths:
                            with open(path, "rb") as attach:
                                bot.send_document(ID, attach)
                            os.remove(path)
                    print("Переслав!")

                else:
                    print("сплю 10 сек")

                    time.sleep(10)

        except post_box.abort:
            continue
