import gzip
import json
import base64
import boto3 

def lambda_handler(event, context):
    client = boto3.client('ec2')
    
    cw_data = event['awslogs']['data']
    compressed_payload = base64.b64decode(cw_data)
    uncompressed_payload = gzip.decompress(compressed_payload)
    
    payload = json.loads(uncompressed_payload)
    log_events = payload['logEvents']
    
    for i in log_events:
        log_message = i["message"]
        policy_arn = json.loads(log_message)["requestParameters"]["policyArn"]
        role_name = json.loads(log_message)["requestParameters"]["roleName"]

    iam_client = boto3.client("iam")
    delete_role_policy = iam_client.detach_role_policy(
        PolicyArn=policy_arn,
        RoleName=role_name,
    )
