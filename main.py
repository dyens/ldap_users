#!/usr/bin/env python

import os
import re
import argparse
import pprint

from ldap3 import ALL_ATTRIBUTES, AUTO_BIND_NO_TLS, SUBTREE, Connection, Server
from ldap3.core.exceptions import LDAPBindError, LDAPInvalidFilterError


ereg = r'[^@]+@[^@]+\.[^@]+'
def email_type(string):
    if re.match(ereg, string):
        return string
    else:
        raise argparse.ArgumentTypeError('Wrong email')




parser = argparse.ArgumentParser(description='Ldap data')
parser.add_argument('email', type=email_type)


def ldap_connection(username, password):
    '''
    Соединение с ldap
    '''
    return Connection(
        Server(
        os.environ.get('LDAP_PROVIDER_URL'),
        port=636, use_ssl=True),
        auto_bind=AUTO_BIND_NO_TLS,
        read_only=True,
        check_names=True,
        user='zoloto585\\%s' % username,
        password=password)


def get_user_data(username, password, search_filter):
    '''
    Получение данных пользователя по ldap
    '''
    try:
        with ldap_connection(username, password) as connection:
            connection.search(
                search_base='OU=585Gold,DC=zoloto585,DC=int',
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=ALL_ATTRIBUTES,
                get_operational_attributes=True)

            if not connection.response:
                return None
            try:
                uid = connection.response[0]['attributes']['middlename']
            except KeyError:
                uid = None
            name = connection.response[0]['attributes']['displayName']
            department = connection.response[0]['attributes'].get('department')
            position = connection.response[0]['attributes'].get('title')

            return {
                'uid': uid,
                'login':
                connection.response[0]['attributes']['sAMAccountName'],
                'name': name,
                'email': connection.response[0]['attributes']['mail'],
                'department': department,
                'position': position
            }

    except LDAPBindError:
        return None

    except LDAPInvalidFilterError:
        return None


def get_user(username, password):
    '''
    Получение данных пользователя из ldap по логину-паролю
    '''
    search_filter = '(&(samAccountName=%s))' % username
    return get_user_data(username, password, search_filter)


def get_user_by_email(email):
    '''
    Получение данных пользователя из ldap почте
    '''
#    # Обработка особых случаев
#    # Да, это не корпоративно, но вот так...
#    if email == '1@gold.su':
#        return {
#            'uid': None,
#            'login': '1',
#            'name': 'Смирнов Александр Сергеевич',
#            'email': email,
#        }
#
    username = os.environ.get('DEFAULT_USER_FOR_LDAP')
    password = os.environ.get('DEFAULT_PASSWORD_FOR_LDAP')
    search_filter = '(&(mail=%s))' % email
    return get_user_data(username, password, search_filter)


if __name__ == '__main__':
    args = parser.parse_args()
    email = args.email
    data = get_user_by_email(email)
    pprint.pprint(data)

