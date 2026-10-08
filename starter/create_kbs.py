import boto3
import time

client = boto3.client('bedrock-agent', region_name='us-east-1')

role_arn = 'arn:aws:iam::029871447747:role/udacity-agentcore-agentcore-role'
vector_bucket_arn = 'arn:aws:s3vectors:us-east-1:029871447747:bucket/udacity-agentcore-vectors-029871447747-a1d01d10'
policy_bucket = 'udacity-agentcore-policy-docs-029871447747-a1d01d10'
policy_bucket_arn = f"arn:aws:s3:::{policy_bucket}"

kbs = [
    {
        'name': 'novamart-returns-policy-kb',
        'prefix': 'policies/returns/',
        'index': 'returns-policy-index'
    },
    {
        'name': 'novamart-shipping-policy-kb',
        'prefix': 'policies/shipping/',
        'index': 'shipping-policy-index'
    },
    {
        'name': 'novamart-warranty-policy-kb',
        'prefix': 'policies/warranty/',
        'index': 'warranty-policy-index'
    }
]

env_updates = {}

for kb in kbs:
    print(f"Creating KB: {kb['name']}")
    kb_res = client.create_knowledge_base(
        name=kb['name'],
        roleArn=role_arn,
        knowledgeBaseConfiguration={
            'type': 'VECTOR',
            'vectorKnowledgeBaseConfiguration': {
                'embeddingModelArn': 'arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0'
            }
        },
        storageConfiguration={
            'type': 'S3_VECTORS',
            's3VectorsConfiguration': {
                'vectorBucketArn': vector_bucket_arn,
                'indexName': kb['index']
            }
        }
    )
    kb_id = kb_res['knowledgeBase']['knowledgeBaseId']
    print(f"  Created KB ID: {kb_id}")
    
    while True:
        status = client.get_knowledge_base(knowledgeBaseId=kb_id)['knowledgeBase']['status']
        if status == 'ACTIVE':
            break
        time.sleep(2)
        
    ds_res = client.create_data_source(
        knowledgeBaseId=kb_id,
        name=f"{kb['name']}-ds",
        dataSourceConfiguration={
            'type': 'S3',
            's3Configuration': {
                'bucketArn': policy_bucket_arn,
                'inclusionPrefixes': [kb['prefix']]
            }
        }
    )
    ds_id = ds_res['dataSource']['dataSourceId']
    print(f"  Created DS ID: {ds_id}")
    
    print(f"  Syncing DS...")
    client.start_ingestion_job(
        knowledgeBaseId=kb_id,
        dataSourceId=ds_id
    )
    
    if 'returns' in kb['name']:
        env_updates['RETURNS_KB_ID'] = kb_id
    elif 'shipping' in kb['name']:
        env_updates['SHIPPING_KB_ID'] = kb_id
    elif 'warranty' in kb['name']:
        env_updates['WARRANTY_KB_ID'] = kb_id

print("\nENV UPDATES:")
for k, v in env_updates.items():
    print(f"{k}={v}")
