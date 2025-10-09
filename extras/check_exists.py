import boto3

# Make sure you're using the profile in your session
session = boto3.Session(profile_name='StycoBotCollectorProfile')
lambda_client = session.client('lambda', region_name='us-east-2')

# Verify which account you're authenticated as
sts_client = session.client('sts', region_name='us-east-2')
identity = sts_client.get_caller_identity()
print(f"Account ID: {identity['Account']}")
print(f"User/Role ARN: {identity['Arn']}")

# Now try listing functions
try:
    response = lambda_client.list_functions()
    print(f"Number of functions found: {len(response['Functions'])}")
    for func in response['Functions']:
        print(f"  - {func['FunctionName']}")
except Exception as e:
    print(f"Error listing functions: {e}")