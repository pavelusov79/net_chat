import sys
import os
import unittest
sys.path.append(os.path.join(os.getcwd(), '..'))
from common.variables import RESPONSE, ERROR, USER, ACCOUNT_NAME, \
    TIME, ACTION, PRESENCE, DEFAULT_IP_ADDRESS
from client import create_client_data, process_answer


class TestClass(unittest.TestCase):

    def test_client_data(self):
        test = create_client_data()
        test[TIME] = 1.1
        self.assertEqual(test, {ACTION: PRESENCE, TIME: 1.1,
                                USER: {ACCOUNT_NAME: 'Guest'}})

    def test_check_200(self):
        server_address = "127.0.0.1"
        self.assertEqual(process_answer({RESPONSE: 200}),
                         f'200 : успешное соединение с сервером {server_address}')

    def test_check_400(self):
        self.assertEqual(process_answer({RESPONSE: 400, ERROR:
            'Bad Request'}), '400 : Bad Request')

    def test_no_response(self):
        self.assertRaises(ValueError, process_answer,
                          {ERROR: 'Bad Request'})

if __name__ == '__main__':
    unittest.main()

