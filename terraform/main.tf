provider "aws" {
  region = var.aws_region
}

data "aws_caller_identity" "current" {}

# --- Lambda Role ---
resource "aws_iam_role" "lambda_role" {
  name = var.lambda_role_name
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_policy" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# --- Lambda Functions ---
resource "aws_lambda_function" "validate" {
  function_name = var.validate_function_name
  filename      = "${path.module}/lambda/validate.zip"
  handler       = "validate.lambda_handler"
  runtime       = var.lambda_runtime
  role          = aws_iam_role.lambda_role.arn
}

resource "aws_lambda_function" "log_metrics" {
  function_name = var.log_metrics_function_name
  filename      = "${path.module}/lambda/log_metrics.zip"
  handler       = "log_metrics.lambda_handler"
  runtime       = var.lambda_runtime
  role          = aws_iam_role.lambda_role.arn
}

# --- Step Function Role ---
resource "aws_iam_role" "step_role" {
  name = var.step_role_name
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "states.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "step_policy" {
  role       = aws_iam_role.step_role.name
  policy_arn = "arn:aws:iam::aws:policy/AWSStepFunctionsFullAccess"
}

# --- Step Function permission to invoke Lambda ---
resource "aws_iam_policy" "step_invoke_lambda_policy" {
  name        = "stepfunction_invoke_lambda_policy"
  description = "Allow Step Functions to invoke Lambda functions"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["lambda:InvokeFunction"]
      Resource = "arn:aws:lambda:${var.aws_region}:${data.aws_caller_identity.current.account_id}:function:*"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "step_invoke_lambda_attach" {
  role       = aws_iam_role.step_role.name
  policy_arn = aws_iam_policy.step_invoke_lambda_policy.arn
}

# --- Step Function ---
resource "aws_sfn_state_machine" "train_pipeline" {
  name     = var.state_machine_name
  role_arn = aws_iam_role.step_role.arn
  definition = jsonencode({
    Comment = "Training pipeline with validation and metrics logging"
    StartAt = "ValidateData"
    States = {
      ValidateData = {
        Type     = "Task"
        Resource = aws_lambda_function.validate.arn
        Next     = "LogMetrics"
      }
      LogMetrics = {
        Type     = "Task"
        Resource = aws_lambda_function.log_metrics.arn
        End      = true
      }
    }
  })
}

# --- Outputs ---
output "step_function_arn" {
  value = aws_sfn_state_machine.train_pipeline.arn
}

output "lambda_validate_arn" {
  value = aws_lambda_function.validate.arn
}

output "lambda_log_metrics_arn" {
  value = aws_lambda_function.log_metrics.arn
}

output "account_id" {
  value       = data.aws_caller_identity.current.account_id
  description = "Current AWS account ID"
}
