import boto3

# First, assume the cross-account role
collector_session = boto3.Session(profile_name='StycoBotCollectorProfile')
sts_client = collector_session.client('sts')

# Assume role in main account
assumed_role = sts_client.assume_role(
    RoleArn='arn:aws:iam::645013853702:role/CrossAccountLambdaAccess',
    RoleSessionName='StycoBot-Access'
)

# Create session with assumed role credentials
main_session = boto3.Session(
    aws_access_key_id=assumed_role['Credentials']['AccessKeyId'],
    aws_secret_access_key=assumed_role['Credentials']['SecretAccessKey'],
    aws_session_token=assumed_role['Credentials']['SessionToken']
)

# Now access Lambda in main account
lambda_client = main_session.client('lambda', region_name='us-east-2')
response = lambda_client.get_function(FunctionName='StycoBot')
print(f"Found function: {response['Configuration']['FunctionName']}")