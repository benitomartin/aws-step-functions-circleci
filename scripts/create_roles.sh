#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -eu

# Load environment variables from .env file
set -o allexport
source .env
set +o allexport

echo "✅ Environment variables loaded."

# Create Lambda Execution Role
echo "🔹 Checking if Lambda Execution Role exists..."

if aws iam get-role --role-name $LAMBDA_ROLE_NAME 2>/dev/null; then
  echo "✅ Lambda Role '$LAMBDA_ROLE_NAME' already exists. Skipping creation."
else
  echo "🔹 Creating Lambda Execution Role..."

  aws iam create-role --role-name $LAMBDA_ROLE_NAME \
    --assume-role-policy-document '{
      "Version": "2012-10-17",
      "Statement": [{
        "Effect": "Allow",
        "Principal": { "Service": "lambda.amazonaws.com" },
        "Action": "sts:AssumeRole"
      }]
    }'

  aws iam attach-role-policy --role-name $LAMBDA_ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

  # aws iam put-role-policy --role-name $LAMBDA_ROLE_NAME \
  #   --policy-name LambdaStartStepFunctionPolicy \
  #   --policy-document '{
  #     "Version": "2012-10-17",
  #     "Statement": [
  #       {
  #         "Effect": "Allow",
  #         "Action": "states:StartExecution",
  #         "Resource": "arn:aws:states:eu-central-1:730335307143:stateMachine:MyStateMachine"
  #       }
  #     ]
  #   }'


  echo "✅ Lambda Role Created"
  
fi

echo ""

# Create Step Functions Execution Role
echo "🔹 Checking if Step Function Role exists..."

if aws iam get-role --role-name $SF_ROLE_NAME 2>/dev/null; then
  echo "✅ Step Function Role '$SF_ROLE_NAME' already exists. Skipping creation."
else
  echo "🔹 Creating Step Function Execution Role..."

  aws iam create-role --role-name $SF_ROLE_NAME \
    --assume-role-policy-document '{
      "Version": "2012-10-17",
      "Statement": [{
        "Effect": "Allow",
        "Principal": { "Service": "states.amazonaws.com" },
        "Action": "sts:AssumeRole"
      }]
    }'

  aws iam put-role-policy --role-name $SF_ROLE_NAME \
    --policy-name StepFunctionLambdaInvokePolicy \
    --policy-document '{
      "Version": "2012-10-17",
      "Statement": [{
        "Effect": "Allow",
        "Action": "lambda:InvokeFunction",
        "Resource": "*"
      }]
    }'

  echo "✅ Step Function Role Created"
fi

echo ""
echo "🎯 All roles are ready!"

