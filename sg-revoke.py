import boto3
import datetime
import os
import json

ec2 = boto3.client('ec2')
logs = boto3.client('logs')
config = boto3.client('config')

def handler(event, context):
    # 환경 변수에서 필요한 값들을 가져오기
    LOG_GROUP_NAME = os.environ['LOG_GROUP_NAME']
    STREAM_NAME = os.environ['STREAM_NAME']
    INSTANCE_ID = os.environ['INSTANCE_ID']
    CONFIG_RULE_NAME = os.environ['CONFIG_RULE_NAME']
    
    # Describe instances to get security groups
    response = ec2.describe_instances(InstanceIds=[INSTANCE_ID])
    security_groups = response['Reservations'][0]['Instances'][0]['SecurityGroups']
    
    # Assuming the instance has only one security group attached
    security_group_id = security_groups[0]['GroupId']
    
    # Define allowed ports
    allowed_inbound_ports = [22, 80]
    allowed_outbound_ports = [22, 80, 443]
    
    # Initialize compliance status
    compliance_type = 'COMPLIANT'
    
    # Check inbound rules
    response_sg = ec2.describe_security_groups(GroupIds=[security_group_id])
    inbound_rules = response_sg['SecurityGroups'][0]['IpPermissions']
    for rule in inbound_rules:
        if 'FromPort' in rule and 'ToPort' in rule:
            for port in range(rule['FromPort'], rule['ToPort'] + 1):
                if port not in allowed_inbound_ports:
                    compliance_type = 'NON_COMPLIANT'
                    ec2.revoke_security_group_ingress(GroupId=security_group_id, IpPermissions=[rule])
                    log_message = f"{datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y-%m-%d-%H:%M:%S')} Inbound {port} Deleted Port!"
                    logs.put_log_events(
                        logGroupName=LOG_GROUP_NAME,
                        logStreamName=STREAM_NAME,
                        logEvents=[{
                            'timestamp': int(datetime.datetime.now().timestamp() * 1000),
                            'message': log_message
                        }]
                    )
                    break  # No need to check further, already non-compliant
        else:
            compliance_type = 'NON_COMPLIANT'
            ec2.revoke_security_group_ingress(GroupId=security_group_id, IpPermissions=[rule])
            log_message = f"{datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y-%m-%d-%H:%M:%S')} Inbound rule without specified port range deleted!"
            logs.put_log_events(
                logGroupName=LOG_GROUP_NAME,
                logStreamName=STREAM_NAME,
                logEvents=[{
                    'timestamp': int(datetime.datetime.now().timestamp() * 1000),
                    'message': log_message
                }]
            )
            break  # No need to check further, already non-compliant

    # Check outbound rules
    outbound_rules = response_sg['SecurityGroups'][0]['IpPermissionsEgress']
    for rule in outbound_rules:
        if 'FromPort' in rule and 'ToPort' in rule:
            for port in range(rule['FromPort'], rule['ToPort'] + 1):
                if port not in allowed_outbound_ports:
                    compliance_type = 'NON_COMPLIANT'
                    ec2.revoke_security_group_egress(GroupId=security_group_id, IpPermissions=[rule])
                    log_message = f"{datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y-%m-%d-%H:%M:%S')} Outbound {port} Deleted Port!"
                    logs.put_log_events(
                        logGroupName=LOG_GROUP_NAME,
                        logStreamName=STREAM_NAME,
                        logEvents=[{
                            'timestamp': int(datetime.datetime.now().timestamp() * 1000),
                            'message': log_message
                        }]
                    )
                    break  # No need to check further, already non-compliant
        else:
            compliance_type = 'NON_COMPLIANT'
            ec2.revoke_security_group_egress(GroupId=security_group_id, IpPermissions=[rule])
            log_message = f"{datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y-%m-%d-%H:%M:%S')} Outbound rule without specified port range deleted!"
            logs.put_log_events(
                logGroupName=LOG_GROUP_NAME,
                logStreamName=STREAM_NAME,
                logEvents=[{
                    'timestamp': int(datetime.datetime.now().timestamp() * 1000),
                    'message': log_message
                }]
            )
            break  # No need to check further, already non-compliant

    # Update AWS Config with the compliance status
    config.put_evaluations(
        Evaluations=[
            {
                'ComplianceResourceType': 'AWS::EC2::Instance',
                'ComplianceResourceId': INSTANCE_ID,
                'ComplianceType': compliance_type,
                'OrderingTimestamp': datetime.datetime.now()
            },
        ],
        ResultToken=event["resultToken"]
    )
    
    return {
        'statusCode': 200,
        'body': 'Security group rules checked and evaluated.'
    }
