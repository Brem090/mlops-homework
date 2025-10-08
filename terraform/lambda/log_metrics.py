import json

def lambda_handler(event, context):
    print("Logging metrics...")
    result = {"status": "success", "message": "Metrics logged successfully"}
    return {
        "statusCode": 200,
        "body": json.dumps(result)
    }