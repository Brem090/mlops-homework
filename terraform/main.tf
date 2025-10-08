provider "aws" {
  region = "eu-north-1"
}

data "aws_caller_identity" "current" {}

resource "aws_iam_role" "lambda_role" {
  name = "lambda_exec_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# Дозволяємо Lambda писати логи в CloudWatch
resource "aws_iam_role_policy_attachment" "lambda_policy" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "validate" {
  function_name = "validate-fn"
  filename      = "${path.module}/lambda/validate.zip"
  handler       = "validate.lambda_handler"
  runtime       = "python3.9"
  role          = aws_iam_role.lambda_role.arn
}

resource "aws_lambda_function" "log_metrics" {
  function_name = "log-metrics-fn"
  filename      = "${path.module}/lambda/log_metrics.zip"
  handler       = "log_metrics.lambda_handler"
  runtime       = "python3.9"
  role          = aws_iam_role.lambda_role.arn
}

resource "aws_iam_role" "step_role" {
  name = "stepfunction_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "states.amazonaws.com"
      }
    }]
  })
}

# Основна політика для Step Functions
resource "aws_iam_role_policy_attachment" "step_policy" {
  role       = aws_iam_role.step_role.name
  policy_arn = "arn:aws:iam::aws:policy/AWSStepFunctionsFullAccess"
}

resource "aws_iam_policy" "step_invoke_lambda_policy" {
  name        = "stepfunction_invoke_lambda_policy"
  description = "Allow Step Functions to invoke Lambda functions"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = "arn:aws:lambda:eu-north-1:${data.aws_caller_identity.current.account_id}:function:*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "step_invoke_lambda_attach" {
  role       = aws_iam_role.step_role.name
  policy_arn = aws_iam_policy.step_invoke_lambda_policy.arn
}

resource "aws_sfn_state_machine" "train_pipeline" {
  name     = "TrainModelPipeline"
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

output "account_id" {
  value       = data.aws_caller_identity.current.account_id
  description = "Current AWS account ID"
}

output "step_function_arn" {
  value       = aws_sfn_state_machine.train_pipeline.arn
  description = "ARN of the Step Function pipeline"
}

output "lambda_validate_arn" {
  value       = aws_lambda_function.validate.arn
  description = "ARN of the Validate Lambda"
}

output "lambda_log_metrics_arn" {
  value       = aws_lambda_function.log_metrics.arn
  description = "ARN of the LogMetrics Lambda"
}
