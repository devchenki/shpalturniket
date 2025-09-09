#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TurboPing - Продвинутая система сетевого мониторинга
Авторские права (c) 2025 Shpalych Technologies. Все права защищены.

Функциональность сетевого пинга для системы мониторинга турникетов.
"""

import ping3
from ping3 import ping, verbose_ping
from pythonping import ping
import json
import Read_config
import os
import subprocess
import concurrent.futures
import threading


ping3.EXCEPTIONS = True

class Ping_IP():
    def ping_ip(self, ip):
        """Простой пинг одного IP адреса"""
        try:
            ping3.verbose_ping(ip, count=1)
            return True  # Успешный пинг
        except ping3.errors.PingError:
            return False  # Неудачный пинг
        except Exception:
            return None  # Ошибка пинга
    
    def ping_all_concurrent(self, data_turnstile, turnstile_list):
        """Пинг всех устройств параллельно для ускорения проверки статуса"""
        results = []
        
        def ping_device(turnstile_number):
            a = data_turnstile[turnstile_number]
            if 2 in a:
                ip = a[0]
                location_turnstile = a[1]
                try:
                    ping3.verbose_ping(ip, count=1, timeout=1)
                    return ['Турникет' + " " + turnstile_number + " / " + location_turnstile + " - " + 'На связи']
                except ping3.errors.PingError:
                    print (ip + '...' + 'offline')
                    return ['Турникет' + " " + turnstile_number + " / " + location_turnstile + " - " + 'Не отвечает']
                except Exception as e:
                    print(f"Error pinging {ip}: {e}")
                    return ['Турникет' + " " + turnstile_number + " / " + location_turnstile + " - " + 'Не отвечает']
            else:
                return None
        
        # Используем ThreadPoolExecutor для параллельного пинга
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # Создаем задачи для всех устройств
            future_to_device = {executor.submit(ping_device, device): device for device in turnstile_list}
            
            # Собираем результаты
            for future in concurrent.futures.as_completed(future_to_device):
                result = future.result()
                if result:
                    results.append(result)
        
        print ('--------------')
        return results
    
    def status_ping(self, data_turnstile, turnstile_list):  # Статус UP/DOWN
        state_connect = []
        for turnstile_number in turnstile_list:
            a = data_turnstile[turnstile_number]
            if 2 in a:
                ip = a[0]
                location_turnstile = a[1]
                try:
                    ping3.verbose_ping(ip, count=1)
                    result = ['Турникет' + " " + turnstile_number + " / " + location_turnstile + " - " + 'На связи']
                except ping3.errors.PingError:
                    print (ip + '...' + 'offline')
                    result = ['Турникет' + " " + turnstile_number + " / " + location_turnstile + " - " + 'Не отвечает']
                state_connect.append(result)
            else:
                continue
        print ('--------------')
        return state_connect

    def statusUP_ping(self, data_turnstile, turnstile_list):
        state_connect_UP = []
        for turnstile_number in turnstile_list:
            a = data_turnstile[turnstile_number]
            if 2 in a:
                ip = a[0]
                location_turnstile = a[1]
                try:
                    ping3.verbose_ping(ip, count=1)
                    result = ['Турникет' + " " + turnstile_number + " / " + location_turnstile + " - " + 'На связи']
                except:
                    print(ip + '...' + 'offline')
                    continue
                state_connect_UP.append(result)
            else:
                continue
        print('--------------')
        return state_connect_UP

    def statusDOWN_ping(self, data_turnstile, turnstile_list):
        counter = 0
        state_connect_DOWN = []
        for turnstile_number in turnstile_list:
            a = data_turnstile[turnstile_number]
            if 2 in a:
                ip = a[0]
                location_turnstile = a[1]
                result = ping_down(ip, turnstile_number, location_turnstile, counter)
                if not result:
                    continue
                # try:
                #     ping3.verbose_ping(ip, count=1)
                #     continue
                # except:
                #     print(ip + '...' + 'offline')
                #     result = ['Турникет' + " " + turnstile_number + " / " + location_turnstile + " - " + 'Не отвечает']
                state_connect_DOWN.append(result)
            else:
                continue
        print('--------------')
        return state_connect_DOWN



def ping_down(ip,turnstile_number, location_turnstile, counter):

    result = []
    try:
        ping3.verbose_ping(ip, count=1)
    except:
        counter += 1

        if counter >= 4:
            print(ip + '...' + 'offline')
            return ['Турникет' + " " + turnstile_number + " / " + location_turnstile + " - " + 'Не отвечает']

        else:
            return ping_down(ip,turnstile_number, location_turnstile, counter)

    return result



# if __name__ == '__main__':
#     a = statusDOWN_ping()
#


    # ip = Ping_IP()
    # print (ip.statusUP_ping(data_turnstile, turnstile_list))