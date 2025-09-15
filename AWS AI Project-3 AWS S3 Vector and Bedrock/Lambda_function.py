import json
import boto3
import os

bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')
KNOWLEDGE_BASE_ID = os.environ.get('KNOWLEDGE_BASE_ID')
GENERATION_MODEL_ARN = "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-micro-v1:0"

def lambda_handler(event, context):
    try:
  
        body = json.loads(event['body'])
        user_query = body.get('query', '')

        if not user_query:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Query parameter is missing.'})
            }

        if not KNOWLEDGE_BASE_ID:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'KNOWLEDGE_BASE_ID environment variable is not set.'})
            }

        print(f"Received query: {user_query}")
        response = bedrock_agent_runtime.retrieve_and_generate(
            input={
                'text': user_query
            },
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': KNOWLEDGE_BASE_ID,
                    'modelArn': GENERATION_MODEL_ARN
                }
            }
        )

        answer = response['output']['text']
        citations = []
        
        if 'citations' in response:
            for citation in response['citations']:
                if 'retrievedReferences' in citation:
                    for ref in citation['retrievedReferences']:
                        if 'content' in ref and 'text' in ref['content']:
                            citations.append(ref['content']['text'])
                       
                        if 'location' in ref and 's3Location' in ref['location']:
                             s3_loc = ref['location']['s3Location']
                             citations.append(f"Source: s3://{s3_loc['uri']}") 

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*' 
            },
            'body': json.dumps({
                'query': user_query,
                'answer': answer,
                'citations': citations
            })
        }

    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }
