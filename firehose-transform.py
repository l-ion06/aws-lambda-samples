import json
import base64

output = []

def lambda_handler(event, context):
    
    for record in event['records']:
        payload = base64.b64decode(record['data']).decode('utf-8')
        data = json.loads(payload)

        transformed_data = transform_data(data)
        payload = str(transformed_data)
        
        add_newline = payload + "\n"
        add_newline = base64.b64encode(add_newline.encode('utf-8'))
        
        output_record = {
            'recordId': record['recordId'],
            'result': 'Ok',
            'data': add_newline
        }
        output.append(output_record)

    return {'records': output}

def transform_data(data):
##########   해당 부분만 수정 하면 된다.   ##########
    data_list        = data['log']

    data_split   = data_list.split()
    data_start   = data_split[3:]

    ip          = data_start[9]
    req_time    = data_start[7]
    ori_msg     = ' '.join(data_start)

    transformed_data = {
        "ip": ip,
        "req_time": req_time,
        "ori_msg": ori_msg
    }

    return transformed_data
#####################################################
