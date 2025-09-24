import boto3
import csv
import json
from datetime import datetime, timedelta
import time

def get_cloudwatch_logs(
    log_group_name,
    start_time_days_ago=7,
    region='us-east-1',
    profile_name=None
):
    """
    Export CloudWatch logs to CSV format
    
    Args:
        log_group_name: Name of your Lambda's log group (e.g., '/aws/lambda/your-function-name')
        start_time_days_ago: How many days back to fetch logs
        output_file: Output CSV filename
        region: AWS region
        profile_name: AWS profile name (use for SSO)
    """
    
    # Initialize CloudWatch Logs client with optional profile
    if profile_name:
        session = _get_assumed_role_session()
        logs_client = session.client('logs', region_name=region)
    else:
        logs_client = boto3.client('logs', region_name=region)
    
    # Calculate time range
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=start_time_days_ago)
    
    # Convert to milliseconds since epoch
    start_timestamp = int(start_time.timestamp() * 1000)
    end_timestamp = int(end_time.timestamp() * 1000)
    
    print(f"Fetching logs from {start_time} to {end_time}")
    
    # Start the query
    query = """
    fields @timestamp, @message, @logStream
    | sort @timestamp desc
    """
    
    response = logs_client.start_query(
        logGroupName=log_group_name,
        startTime=start_timestamp,
        endTime=end_timestamp,
        queryString=query
    )
    
    query_id = response['queryId']
    print(f"Started query with ID: {query_id}")
    
    # Wait for query to complete
    while True:
        result = logs_client.get_query_results(queryId=query_id)
        if result['status'] == 'Complete':
            break
        elif result['status'] == 'Failed':
            print("Query failed!")
            return
        print("Query running...")
        time.sleep(2)
    
    return result
    
def logs_to_csv(result, output_file):
    # Process results and write to CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['timestamp', 'log_stream', 'message', 'parsed_data']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        
        for result_row in result['results']:
            row_data = {}
            parsed_message = {}
            
            # Extract fields from the result
            for field in result_row:
                if field['field'] == '@timestamp':
                    # Convert timestamp to readable format
                    timestamp = datetime.fromisoformat(field['value'].replace('Z', '+00:00'))
                    row_data['timestamp'] = timestamp.strftime('%Y-%m-%d %H:%M:%S')
                elif field['field'] == '@logStream':
                    row_data['log_stream'] = field['value']
                elif field['field'] == '@message':
                    message = field['value']
                    row_data['message'] = message.replace("\r", "").replace("\n", "\\n")  # normalize
                    
                    # Try to parse JSON messages
                    try:
                        parsed_message = json.loads(message)
                        row_data['parsed_data'] = json.dumps(parsed_message, separators=(',', ':'))
                    except (json.JSONDecodeError, TypeError):
                        # If not JSON, try to extract common patterns
                        if 'RequestId:' in message:
                            # Extract request ID and other common Lambda fields
                            parts = message.split('\t')
                            for part in parts:
                                if 'RequestId:' in part:
                                    parsed_message['request_id'] = part.split(':', 1)[1].strip()
                                elif 'Duration:' in part:
                                    parsed_message['duration'] = part.split(':', 1)[1].strip()
                                elif 'Billed Duration:' in part:
                                    parsed_message['billed_duration'] = part.split(':', 1)[1].strip()
                                elif 'Memory Size:' in part:
                                    parsed_message['memory_size'] = part.split(':', 1)[1].strip()
                        
                        row_data['parsed_data'] = json.dumps(parsed_message) if parsed_message else ''
            
            writer.writerow(row_data)
    
    print(f"Exported {len(result['results'])} log entries to {output_file}")

def _get_assumed_role_session():
    """Assume role for local execution"""
    # Use profile to get account ID dynamically
    local_session = boto3.Session(profile_name='local-script')
    sts_client = local_session.client('sts')
    
    # Get current account ID
    identity = sts_client.get_caller_identity()
    account_id = identity['Account']
    
    # Build role ARN dynamically
    role_arn = f'arn:aws:iam::{account_id}:role/StycoBotCollector-role'
    
    assumed_role = sts_client.assume_role(
        RoleArn=role_arn,
        RoleSessionName='local-metrics-session'
    )
    
    credentials = assumed_role['Credentials']
    
    return boto3.Session(
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken']
    )

def process_logs(logs):
    # Process logs here.
    return logs

def export_cloudwatch_logs_to_csv(
    log_group_name,
    start_time_days_ago=7,
    output_file='cloudwatch_logs.csv',
    region='us-east-1',
    profile_name=None
):
    logs = get_cloudwatch_logs(log_group_name, start_time_days_ago, region, profile_name)
    if logs is None:
        print('Error: Could not fetch logs')
    processed_logs = process_logs(logs)
    if logs is None:
        print('Error: Could not process logs')
    logs_to_csv(processed_logs, output_file)

# Example usage
if __name__ == "__main__":
    # Replace with your actual values
    LAMBDA_FUNCTION_NAME = "StycoBot"
    LOG_GROUP_NAME = f"/aws/lambda/{LAMBDA_FUNCTION_NAME}"
    AWS_REGION = "us-east-2"
    
    SSO_PROFILE = 'local-script'
    
    # Export logs
    export_cloudwatch_logs_to_csv(
        log_group_name=LOG_GROUP_NAME,
        start_time_days_ago=7,
        output_file='output/lambda_logs.csv',
        region=AWS_REGION,
        profile_name=SSO_PROFILE
    )
    
    # Export metrics(Future!)
    # export_cloudwatch_metrics_to_csv(
    #     function_name=LAMBDA_FUNCTION_NAME,
    #     start_time_days_ago=7,
    #     output_file='lambda_metrics.csv',
    #     region=AWS_REGION,
    #     profile_name=SSO_PROFILE
    # )