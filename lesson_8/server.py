import datetime
import logging
import select
import socket
import sys
import json
from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, \
    PRESENCE, TIME, USER, ERROR, DEFAULT_PORT, DEFAULT_IP_ADDRESS, MESSAGE, MESSAGE_TEXT, SENDER,\
    DESTINATION, EXIT
from common.utils import get_message, send_message
from log.config_log.decos import log
from log.config_log import config_server_log

#Инициализация логирования сервера.
SERVER_LOGGER = logging.getLogger('server')


@log
def process_client_message(message, messages, client, clients, names):
    SERVER_LOGGER.debug(f'Сообщение от клиента {ACCOUNT_NAME}: {message}')
    print(f'Сообщение от клиента {ACCOUNT_NAME}: {message}')
    if ACTION in message and message[ACTION] == PRESENCE and TIME in \
            message and USER in message:
        print(f'Клиент {ACCOUNT_NAME} подключен')
        if message[USER][ACCOUNT_NAME] not in names.keys():
            names[message[USER][ACCOUNT_NAME]] = client
            send_message(client, {RESPONSE: 200})
        # else:
        #     response = {RESPONSE: 400, ERROR: 'Bad Request'}
        #     response[ERROR] = 'Имя пользователя уже занято.'
        #     send_message(client, response)
        #     clients.remove(client)
        #     client.close()
        # return
    elif ACTION in message and message[ACTION] == MESSAGE and \
         TIME in message and MESSAGE_TEXT in message:
        messages.append(message)
        return
        # Если клиент выходит
    elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
        clients.remove(names[message[ACCOUNT_NAME]])
        names[message[ACCOUNT_NAME]].close()
        del names[message[ACCOUNT_NAME]]
        return
    else:
        send_message(client, {
            RESPONSE: 400,
            ERROR: 'Bad Request'
        })
        return


@log
def process_message(message, names, listen_socks):
    """
    Функция адресной отправки сообщения определённому клиенту. Принимает словарь сообщение,
    список зарегистрированых пользователей и слушающие сокеты. Ничего не возвращает.
    :param message:
    :param names:
    :param listen_socks:
    :return:
    """
    if message[DESTINATION] in names and names[message[DESTINATION]] in listen_socks:
        send_message(names[message[DESTINATION]], message)
        SERVER_LOGGER.info(f'Отправлено сообщение пользователю {message[DESTINATION]} '
                    f'от пользователя {message[SENDER]}.')
    elif message[DESTINATION] in names and names[message[DESTINATION]] not in listen_socks:
        raise ConnectionError
    else:
        SERVER_LOGGER.error(f'Пользователь {message[DESTINATION]} не зарегистрирован на сервере, '
            f'отправка сообщения невозможна.')


@log
def main():
    """
    Загрузка параметров командной строки, если нет параметров, то задаём значения по умоланию.
    Сначала обрабатываем порт:
    server.py -p 8079 -a 192.168.1.2
    :return:
    """
    try:
        if '-p' in sys.argv:
            port = int(sys.argv[sys.argv.index('-p') + 1])
        else:
            port = DEFAULT_PORT
        if port < 1024 or port > 65535:
            SERVER_LOGGER.critical(f'Попытка запуска сервера с указанием неподходящего порта '
                                   f'{port}. Допустимы адреса с 1024 до 65535.')
            raise ValueError
    except IndexError:
        SERVER_LOGGER.critical('Попытка запуска сервера без указания порта. После параметра '
                               '-\'p\' необходимо указать номер порта.')
        print('После параметра -\'p\' необходимо указать номер порта.')
        sys.exit(1)
    except ValueError:
        print('В качастве порта может быть указано только число в '
              'диапазоне от 1024 до 65535.')
        sys.exit(1)

    # Затем загружаем какой адрес слушать
    try:
        if '-a' in sys.argv:
            address = sys.argv[sys.argv.index('-a') + 1]
        else:
            address = DEFAULT_IP_ADDRESS
        print(f'запущен сервер {address}')
        SERVER_LOGGER.info(f'Запущен сервер, порт для подключений: {port}, '
                       f'адрес с которого принимаются подключения: {address}.')
    except IndexError:
        SERVER_LOGGER.critical('Попытка запуска сервера без указания адреса клиента. После '
                               'параметра -\'a\' необходимо указать адрес клиента.')
        print('После параметра \'a\'- необходимо указать адрес, '
              'который будет слушать сервер.')
        sys.exit(1)

    # Готовим сокет
    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.bind((address, port))
    transport.settimeout(1)

    # список клиентов , очередь сообщений
    clients = []
    messages = []

    # Слушаем порт
    transport.listen(MAX_CONNECTIONS)

    while True:
        try:
            client, client_address = transport.accept()
        except OSError:
            pass
        else:
            SERVER_LOGGER.info(f'Установлено соединение с ПК {client_address}')
            clients.append(client)

        recv_data_lst = []
        send_data_lst = []
        err_lst = []
        names = dict()

        # Проверяем на наличие ждущих клиентов
        try:
            if clients:
                recv_data_lst, send_data_lst, err_lst = select.select(clients, clients, [], 0)
        except OSError:
            pass
            # принимаем сообщения и если там есть сообщения,
            # кладём в словарь, если ошибка, исключаем клиента.
            if recv_data_lst:
                for client_with_message in recv_data_lst:
                    try:
                        process_client_message(get_message(client_with_message),
                                               messages, clients, names, client_with_message)
                    except:
                        SERVER_LOGGER.info(f'Клиент {client_with_message.getpeername()} '
                                    f'отключился от сервера.')
                        clients.remove(client_with_message)

            for i in messages:
                try:
                    process_message(i, names, send_data_lst)
                except Exception:
                    SERVER_LOGGER.info(f'Связь с клиентом с именем {i[DESTINATION]} была потеряна')
                    clients.remove(names[i[DESTINATION]])
                    del names[i[DESTINATION]]
            messages.clear()


if __name__ == '__main__':
    main()
