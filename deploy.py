import json
import os
from typing import Any

import boto3
import dotenv  # type: ignore
from loguru import logger

dotenv.load_dotenv()

AWS_ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID")
SF_ROLE_NAME = os.getenv("SF_ROLE_NAME")
LAMBDA_ROLE_NAME = os.getenv("LAMBDA_ROLE_NAME")
LAMBDA_FOLDER = os.getenv("LAMBDA_FOLDER")
LAMBDA_FUNCTION_ONE = os.getenv("LAMBDA_FUNCTION_ONE")
LAMBDA_FUNCTION_TWO = os.getenv("LAMBDA_FUNCTION_TWO")


lambda_client = boto3.client('lambda')
sf_client = boto3.client('stepfunctions')

def create_lambda_function(name: str, 
                         zip_path: str, 
                         role_arn: str, 
                         handler: str) -> str:
    if not os.path.exists(zip_path):
        raise FileNotFoundError(f"{zip_path} does not exist. Make sure to zip your code first.")

    with open(zip_path, 'rb') as f:
        zipped_code = f.read()

    try:
        lambda_client.get_function(FunctionName=name)
        logger.info(f"✅ Lambda function {name} already exists. Updating code...")

        response = lambda_client.update_function_code(
            FunctionName=name,
            ZipFile=zipped_code
        )
    except lambda_client.exceptions.ResourceNotFoundException:
        logger.info(f"🚀 Creating new Lambda function {name}...")

        response = lambda_client.create_function(
            FunctionName=name,
            Runtime='python3.12',
            Role=role_arn,
            Handler=handler,
            Code={'ZipFile': zipped_code},
            Timeout=10
        )

    return str(response['FunctionArn'])


def deploy_state_machine(def_path: str, 
                         role_arn: str, 
                         lambdas: dict[str, str], 
                         state_machine_name: str = "MyStateMachine") -> dict[str, Any]:
    with open(def_path) as f:
        definition = json.load(f)

    # Convert JSON object to string
    definition_str = json.dumps(definition)

    # Replace placeholders with real Lambda ARNs
    definition_str = definition_str.replace("TASK_ONE_LAMBDA_ARN", lambdas['TaskOne'])
    definition_str = definition_str.replace("TASK_TWO_LAMBDA_ARN", lambdas['TaskTwo'])

    # Now deploy
    existing_machines = sf_client.list_state_machines()['stateMachines']
    logger.info(f"Found {len(existing_machines)} existing state machines.")
    logger.info(f"Existing machines: {existing_machines}")

    state_machine_arn = None
    for sm in existing_machines:
        if sm['name'] == state_machine_name:
            state_machine_arn = sm['stateMachineArn']
            break

    if state_machine_arn:
        logger.info(f"✅ State Machine {state_machine_name} already exists. Updating...")
        response = sf_client.update_state_machine(
            stateMachineArn=state_machine_arn,
            definition=definition_str,
            roleArn=role_arn
        )
    else:
        logger.info(f"🚀 Creating new State Machine {state_machine_name}...")
        response = sf_client.create_state_machine(
            name=state_machine_name,
            definition=definition_str,
            roleArn=role_arn,
            type="STANDARD"
        )

    return dict(response)


if __name__ == "__main__":
    logger.info("Starting deployment...")

    lambda_role = f"arn:aws:iam::{AWS_ACCOUNT_ID}:role/{LAMBDA_ROLE_NAME}"
    sf_role = f"arn:aws:iam::{AWS_ACCOUNT_ID}:role/{SF_ROLE_NAME}"

    # Create or update Lambdas and add S3 trigger for TaskOne
    lambdas = {
        "TaskOne": create_lambda_function(
            LAMBDA_FUNCTION_ONE,  # type: ignore
            f"{LAMBDA_FOLDER}/task_one.zip",
            lambda_role,
            "app_task_one.lambda_handler",
        ),
        "TaskTwo": create_lambda_function(
            LAMBDA_FUNCTION_TWO,  # type: ignore
            f"{LAMBDA_FOLDER}/task_two.zip",
            lambda_role,
            "app_task_two.lambda_handler"
        )
    }

    deploy_state_machine("state_machine_definition.json", sf_role, lambdas)
    logger.info("Deployment complete!")
