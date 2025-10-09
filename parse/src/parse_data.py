import pandas as pd
import json
from datetime import datetime
from collections import defaultdict

def flatten_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    For now just calls groupby, but it can expand later.
    """
    return df.groupby("session_id").first()

def find_session_count_month(df: pd.DataFrame):
    df['timestamp'] = pd.to_datetime(df['timestamp']) 
    monthly_counts = df.groupby(df['timestamp'].dt.strftime('%Y-%m')).size()
    return list(monthly_counts.items())

def parse_lambda_logs(csv_file_path):
    """
    Parse AWS Lambda logs and extract:
    1. Active users per month (based on unique session_ids)
    2. Average Full Event Processing duration per month
    """
    
    # Read the CSV file
    df = pd.read_csv(csv_file_path, sep=',')
    
    # Name the columns
    df.columns = ['timestamp', 'log_stream', 'message', 'parsed_data'] + \
                 [f'col_{i}' for i in range(len(df.columns) - 4)]
    
    # Parse all relevant log entries
    parsed_logs = []
    for idx, row in df.iterrows():
        try:
            message = row['message']

            # we want to ignore rows that aren't strings
            if not isinstance(message, str):
                continue
            
            # We want to add rows that are just summary lines as is
            if message.strip().startswith("REPORT") or message.strip().startswith("START") or message.strip().startswith("END"):
                continue


            message = message.strip('\\n')
            try:
                # Try to parse JSON
                data = json.loads(message)            
            except json.JSONDecodeError:
                # Not JSON so skip it
                continue


            timestamp = data.get('timestamp', '')
            event_type = data.get('event_type', '')
            session_id = data.get('session_id', '')
            data = data.get('data', '')

            log_entry = {
                'timestamp': timestamp,
                'event_type': event_type,
                'session_id': session_id,
                'data': data
            }
            
            # Extract duration for Full Event Processing
            if event_type == 'metric_recorded':
                metric_name = data.get('data', {}).get('metric_name', '')
                if 'Full Event Processing_duration' in metric_name:
                    log_entry['duration'] = data.get('data', {}).get('value', 0)
            # We will add more parsing as needed. 

            parsed_logs.append(log_entry)
            
        except (json.JSONDecodeError, AttributeError, KeyError) as e:
            print("ERROR", e)
            continue
    
    logs_df = pd.DataFrame(parsed_logs)
    # logs_df.columns =  
    if logs_df.empty:
        return {
            'active_users_per_month': [],
            'avg_processing_time_per_month': []
        }
    
    # logs_df = group_data(logs_df, "session_id")
    print(logs_df.columns)

    # session_group = df.groupby('session_id')
    # total_sessions = session_group.ngroups
    
    flattened_df = flatten_df(logs_df)
    month_to_sessions = find_session_count_month(flattened_df) 

    # Convert timestamp to datetime
    # logs_df['timestamp'] = pd.to_datetime(logs_df['timestamp'])
    # print('x', logs_df['timestamp'].dt.strftime('%Y-%m'))
    # logs_df['year_month'] = logs_df['timestamp'].dt.strftime('%Y-%m')
    
    # # 1. Active users per month (unique sessions)
    # active_users = logs_df.groupby('year_month')['session_id'].nunique().reset_index()
    # active_users.columns = ['month', 'active_users']
    # active_users_list = active_users.to_dict('records')
    
    # print('HERE', logs_df)
    # # 2. Average Full Event Processing duration per month
    # duration_logs = logs_df[logs_df['duration'].notna()].copy()
    
    # if not duration_logs.empty:
    #     avg_duration = duration_logs.groupby('year_month')['duration'].mean().reset_index()
    #     avg_duration.columns = ['month', 'avg_duration_seconds']
    #     avg_duration['avg_duration_seconds'] = avg_duration['avg_duration_seconds'].round(3)
    #     avg_duration_list = avg_duration.to_dict('records')
    # else:
    #     avg_duration_list = []
    
    # Create output for React app
    output = {
        'month_to_sessions': month_to_sessions
        # 'active_users_per_month': active_users_list,
        # 'avg_processing_time_per_month': avg_duration_list
    }
    
    return output

def main():
    # Parse the logs
    result = parse_lambda_logs('generated_assets/lambda_logs.csv')
    
    # Output as JSON (for React app consumption)
    output_json = json.dumps(result, indent=2)
    print(output_json)
    
    # Save to JSON file
    with open('generated_assets/metrics.json', 'w') as f:
        f.write(output_json)
    
    print("\nMetrics saved to metrics.json")

if __name__ == "__main__":
    main()