import datetime
import json
import threading
import logging
import argparse
import socket
import sys
import time

from log.config_log.decos import log
from log.config_log import config_client_log
from common.utils import get_message, send_message
from common.variables import ACTION, PRESENCE, TIME, USER, \
    ACCOUNT_NAME, RESPONSE, ERROR, DEFAULT_IP_ADDRESS, DEFAULT_PORT,\
    SENDER, MESSAGE, MESSAGE_TEXT, EXIT, DESTINATION

# Инициализация клиентского логера
CLIENT_LOGGER = logging.getLogger('client')


@log
def create_client_data():
    account_name = input("Введите имя пользователя: ")
    if account_name == "":
        account_name = "Guest"
    send = {
        ACTION: PRESENCE,
        TIME: datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
        USER: {
            ACCOUNT_NAME: account_name
        }
    }
    CLIENT_LOGGER.debug(f'Сформировано {PRESENCE} сообщение для пользователя {account_name}')
    return send


@log
def process_answer(message):
    CLIENT_LOGGER.debug(f'Сообщение от сервера {server_address}: {message}')
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return f'200 : успешное соединение с сервером ' \
                   f'{server_address}'
        return f'400 : {message[ERROR]}'
    raise ValueError


@log
def create_message(sock, account_name):
    """Функция запрашивает текст сообщения и возвращает его.
    Так же завершает работу при вводе подобной комманды
    """
    message = input('Введите сообщение для отправки или \'q\' для завершения работы: ')
    to_user = input('Введите получателя сообщения: ')
    if message == 'q':
        # send_message(sock, create_exit_message(account_name))
        sock.close()
        CLIENT_LOGGER.info('Завершение работы по команде пользователя.')
        print('Спасибо за использование нашего сервиса!')
        sys.exit(0)
    message_dict = {
        ACTION: MESSAGE,
        TIME: datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
        ACCOUNT_NAME: account_name,
        DESTINATION: to_user,
        MESSAGE_TEXT: message
    }
    CLIENT_LOGGER.debug(f'Сформирован словарь сообщения: {message_dict}')
    try:
        send_message(sock, message_dict)
        CLIENT_LOGGER.info(f'Отправлено сообщение для пользователя {to_user}')
    except:
        CLIENT_LOGGER.critical('Потеряно соединение с сервером.')
        sys.exit(1)


@log
def message_from_server(sock, username):
    """Функция - обработчик сообщений других пользователей, поступающих с сервера"""
    try:
        message = get_message(sock)
        if ACTION in message and message[ACTION] == MESSAGE and \
                SENDER in message and MESSAGE_TEXT in message and message[DESTINATION] == username:
            print(f'Получено сообщение от пользователя '
                  f'{message[SENDER]}:\n{message[MESSAGE_TEXT]}')
            CLIENT_LOGGER.info(f'Получено сообщение от пользователя'
                        f'{message[SENDER]}:\n{message[MESSAGE_TEXT]}')
        else:
            CLIENT_LOGGER.error(f'Получено некорректное сообщение с сервера: {message}')
    except Exception:
        CLIENT_LOGGER.error(f'Не удалось декодировать полученное сообщение.')
    except (OSError, ConnectionError, ConnectionAbortedError,
            ConnectionResetError, json.JSONDecodeError):
        CLIENT_LOGGER.critical(f'Потеряно соединение с сервером.')


# @log
# def create_exit_message(account_name):
#     """Функция создаёт словарь с сообщением о выходе"""
#     return {
#         ACTION: EXIT,
#         TIME: datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
#         ACCOUNT_NAME: account_name
#     }
#
#
# @log
# def user_interactive(sock, username):
#     """Функция взаимодействия с пользователем, запрашивает команды, отправляет сообщения"""
#     while True:
#         command = input('Введите команду: message - для отправки сообщений или exit для выхода: ')
#         if command == 'message':
#             create_message(sock, username)
#
#         elif command == 'exit':
#             send_message(sock, create_exit_message(username))
#             print('Завершение соединения.')
#             CLIENT_LOGGER.info('Завершение работы по команде пользователя.')
#             # Задержка неоходима, чтобы успело уйти сообщение о выходе
#             time.sleep(0.5)
#             break
#         else:
#             print('Команда не распознана, попробойте снова.')


@log
def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--name', default=None, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    client_name = namespace.name
    return client_name


@log
def main():
    # client.py 192.168.1.2 8079
    client_name = arg_parser()
    try:
        global server_address
        server_address = sys.argv[1]
        server_port = int(sys.argv[2])
        if server_port < 1024 or server_port > 65535:
            CLIENT_LOGGER.critical(f'Попытка запуска клиента с неподходящим номером порта: '
                                   f'{server_port}.')
            raise ValueError
        print(f'Запущен клиент с парамертами: адрес сервера: '
                           f'{server_address}, порт: {server_port}, имя клиента: {client_name}')
        CLIENT_LOGGER.info(f'Запущен клиент с парамертами: адрес сервера: '
                           f'{server_address}, порт: {server_port}, имя клиента: {client_name}')
    except IndexError:
        server_address = DEFAULT_IP_ADDRESS
        server_port = DEFAULT_PORT
    except ValueError:
        print('В качестве порта может быть указано только число в диапазоне от 1024 до 65535.')
        sys.exit(1)

    # Инициализация сокета и обмен

    try:
        shift = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        shift.connect((server_address, server_port))
        message_to_server = create_client_data()
        send_message(shift, message_to_server)
        answer = process_answer(get_message(shift))
        CLIENT_LOGGER.info(f'Принят ответ от сервера {answer}')
        print(f'Принят ответ от сервера {answer}')
    except (ValueError, json.JSONDecodeError):
        CLIENT_LOGGER.error('Не удалось декодировать полученную Json строку.')
        print('Не удалось декодировать сообщение сервера.')
    except (ConnectionRefusedError, ConnectionError):
        CLIENT_LOGGER.critical(f'Не удалось подключиться к серверу {server_address}:{server_port}, '
            f'конечный компьютер отверг запрос на подключение.')
        sys.exit(1)

    else:
        # Если соединение с сервером установлено корректно,
        # запускаем клиенский процесс приёма сообщний
        receiver = threading.Thread(target=message_from_server, args=(shift, client_name))
        receiver.daemon = True
        receiver.start()

        # затем запускаем отправку сообщений и взаимодействие с пользователем.
        user_interface = threading.Thread(target=create_message, args=(shift, client_name))
        user_interface.daemon = True
        user_interface.start()
        CLIENT_LOGGER.debug('Запущены процессы')
        print('Запущены процессы')

        # Watchdog основной цикл, если один из потоков завершён,
        # то значит или потеряно соединение или пользователь
        # ввёл exit. Поскольку все события обработываются в потоках,
        # достаточно просто завершить цикл.
        while True:
            time.sleep(1)
            if receiver.is_alive() and user_interface.is_alive():
                continue
            break


if __name__ == '__main__':
    main()

