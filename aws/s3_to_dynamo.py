import boto3
import json
import concurrent.futures
import time

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('SignifyDictionary')

BUCKET_NAME = 'signify-asl-dictionary-v1'
PREFIX = 'dictionary/'

def migrate_word(file_key):
    try:
        # Extract word from "dictionary/word.json"
        word = file_key.split('/')[-1].replace('.json', '')
        
        # Download from S3
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=file_key)
        json_data = response['Body'].read().decode('utf-8')
        
        # Upload to DynamoDB as a compressed JSON string
        table.put_item(
            Item={
                'word': word,
                'animation_data': json_data
            }
        )
        print(f"[SUCCESS] Migrated {word}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to migrate {file_key}: {e}")
        return False

def main():
    print("Listing all files in S3 bucket...")
    
    paginator = s3_client.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=BUCKET_NAME, Prefix=PREFIX)
    
    file_keys = []
    for page in pages:
        if 'Contents' in page:
            for obj in page['Contents']:
                if obj['Key'].endswith('.json'):
                    file_keys.append(obj['Key'])
                    
    print(f"Found {len(file_keys)} JSON files. Starting high-speed migration...")
    
    start_time = time.time()
    
    # Run with 20 threads to speed up the migration
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(migrate_word, file_keys)
        
    elapsed = time.time() - start_time
    print(f"\n[DONE] Migrated {len(file_keys)} files to DynamoDB in {elapsed:.2f} seconds.")

if __name__ == '__main__':
    main()
