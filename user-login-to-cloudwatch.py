import boto3
import json
import gzip
import os
import time
from io import BytesIO

s3_client = boto3.client('s3')
logs_client = boto3.client('logs')

log_group_name = os.environ['LOG_GROUP_NAME']
log_stream_name = os.environ['LOG_STREAM_NAME']

def lambda_handler(event, context):
    # S3 이벤트에서 버킷 이름과 객체 키를 추출
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    object_key = event['Records'][0]['s3']['object']['key']

    try:
        # S3 객체 다운로드 및 압축 해제
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        compressed_data = response['Body'].read()
        uncompressed_data = gzip.GzipFile(fileobj=BytesIO(compressed_data)).read()
        cloudtrail_events = json.loads(uncompressed_data)
        
        for record in cloudtrail_events['Records']:
            if record['eventName'] == 'ConsoleLogin':
                user_identity = record.get('userIdentity', {})
                user_name = user_identity.get('userName', 'unknown')
                log_message = { 'USER': f'{user_name} has logged in!' }
                # log_message = { 'USER': user_name }
                
                logs_client.put_log_events(
                    logGroupName=log_group_name,
                    logStreamName=log_stream_name,
                    logEvents=[
                        {
                            'timestamp': int(round(time.time() * 1000)),
                            'message': json.dumps(log_message)
                        }
                    ]
                )
                
        print("로그가 성공적으로 기록되었습니다.")
        
    except Exception as e:
        print("로그 기록 중 오류 발생:", e)
        raise e
