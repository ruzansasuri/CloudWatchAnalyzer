import boto3

session = boto3.Session(profile_name='StycoBotCollectorProfile')

# Test basic Lambda access
lambda_client = session.client('lambda', region_name='us-east-2')

print("=== Testing Lambda Access ===")
try:
    response = lambda_client.list_functions()
    print(f"✓ Can list Lambda functions")
    print(f"Functions found: {len(response['Functions'])}")
    
    for func in response['Functions']:
        print(f"  - {func['FunctionName']}")
        
except Exception as e:
    print(f"✗ Cannot list Lambda functions: {e}")

# Test CloudWatch Logs access  
logs_client = session.client('logs', region_name='us-east-2')

print("\n=== Testing CloudWatch Logs Access ===")
try:
    response = logs_client.describe_log_groups(logGroupNamePrefix='/aws/lambda/', limit=10)
    print(f"✓ Can access CloudWatch Logs")
    print(f"Lambda log groups found: {len(response['logGroups'])}")
    
    for lg in response['logGroups']:
        function_name = lg['logGroupName'].replace('/aws/lambda/', '')
        print(f"  - {function_name}")
        
except Exception as e:
    print(f"✗ Cannot access CloudWatch Logs: {e}")