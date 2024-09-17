import json
import boto3
import urllib3
from botocore.exceptions import BotoCoreError, ClientError

def get_alb_endpoint(region_name):
    try:
        elb = boto3.client('elbv2', region_name=region_name)
        response = elb.describe_load_balancers()
        
        alb_dns_names = []
        for lb in response['LoadBalancers']:
            if lb['Type'] == 'application':
                alb_dns_names.append(lb['DNSName'])
        
        return alb_dns_names
    except (BotoCoreError, ClientError) as e:
        print(f"Error fetching ALB endpoint in region {region_name}: {e}")
        return []

def alb_healthcheck(dns_lists, uri_path):
    http = urllib3.PoolManager()
    uri = uri_path.split("/")[2] if len(uri_path.split("/")) > 2 else ""
    
    def check_health(url):
        try:
            response = http.request('GET', f"http://{url}/healthcheck?path={uri}")
            return response.status
        except Exception as e:
            print(f"Health check failed for {url}: {e}")
            return 500
    
    seoul_health = check_health(dns_lists[0]) if len(dns_lists) > 0 else 500
    us_health = check_health(dns_lists[1]) if len(dns_lists) > 1 else 500
    
    response = {
        "seoul": { 
            "state": "healthy" if int(seoul_health) == 200 else "unhealthy",
            "url": f"{dns_lists[0]}" if int(seoul_health) == 200 else ""
        },
        "us": { 
            "state": "healthy" if int(us_health) == 200 else "unhealthy",
            "url": f"{dns_lists[1]}" if int(us_health) == 200 else ""
        }
    }
    
    return response

def lambda_handler(event, context):
    request = event['Records'][0]['cf']['request']
    uri = request['uri']
    
    region_list = ['ap-northeast-2', 'us-east-1']
    region_alb_dns = []
    
    for region in region_list:
        alb_dns_name = get_alb_endpoint(region)
        region_alb_dns.extend(alb_dns_name)
    
    healthcheck_response = alb_healthcheck(region_alb_dns, uri)
    
    if 'origin' not in request:
        request['origin'] = {
            'custom': {
                'domainName': '',
                'port': 80,
                'protocol': 'http',
                'path': ''
            }
        }

    if healthcheck_response["seoul"]["state"] == "healthy":
        request["origin"]["custom"]["domainName"] = healthcheck_response["seoul"]["url"]
    elif healthcheck_response["us"]["state"] == "healthy":
        request["origin"]["custom"]["domainName"] = healthcheck_response["us"]["url"]
    
    # 도메인 이름이 빈 문자열일 경우 예외 처리
    if not request["origin"]["custom"]["domainName"]:
        raise Exception("No healthy ALB found")
    
    return request
