import json


def read_config():
    with open('IP_list.json','r', encoding='utf-8') as f: #('E:\\PycharmProjects\\Ping _test\\venv\\Scripts\\IP_list.json','r', encoding='utf-8')
        data_turnstile = json.load(f)
        # turnstile_list = data_turnstile.keys()
    return data_turnstile


with open('config.json','r', encoding='utf-8') as f: #('E:\\PycharmProjects\\Ping _test\\venv\\Scripts\\config.json','r', encoding='utf-8')
    config = json.load(f)
    TOKEN = config['TOKEN']
    time_connect = int(config['time_connect'])
    # Обрабатываем chat_id как строку или список
    chat_id_raw = config['chat_id']
    if isinstance(chat_id_raw, str):
        chat_id = [cid.strip() for cid in chat_id_raw.split(',') if cid.strip()]
    elif isinstance(chat_id_raw, list):
        chat_id = [str(cid).strip() for cid in chat_id_raw if str(cid).strip()]
    else:
        chat_id = [str(chat_id_raw).strip()] if str(chat_id_raw).strip() else []
#
#
# if __name__ ==  "__main__":
#     a = Read_Config.read_data_connect()
#     b = a.config()
#     print(b)


# class Read_Config():
#
#     def read_data_turnstile(self):
#         with open('E:\\PycharmProjects\\Ping _test\\venv\\Scripts\\IP_list.json','r', encoding='utf-8') as f: #
#             self.data_turnstile = json.load(f)
#             print('mjjkcdbh')
#             # turnstile_list = data_turnstile.keys()
#         return self.data_turnstile
#
#
#     def read_data_connect(self):
#         with open('E:\\PycharmProjects\\Ping _test\\venv\\Scripts\\config.json','r', encoding='utf-8') as f: #
#             self.config = json.load(f)
#             self.TOKEN = config['TOKEN']
#             self.time_connect = int(config['time_connect'])
#             self.chat_id = config['chat_id'].split(',')
#         return self.data_turnstile




if __name__ ==  "__main__":
    a = Read_Config()
    b = a.read_data_turnstile()
    print(b)





