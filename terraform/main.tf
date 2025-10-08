provider "aws" {
  region = "eu-north-1" # або твій регіон
}

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

# Дозвіл Lambda писати логи в CloudWatch
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

resource "aws_iam_role_policy_attachment" "step_policy" {
  role       = aws_iam_role.step_role.name
  policy_arn = "arn:aws:iam::aws:policy/AWSStepFunctionsFullAccess"
}


resource "aws_sfn_state_machine" "train_pipeline" {
  name     = "TrainModelPipeline"
  role_arn = aws_iam_role.step_role.arn

  definition = jsonencode({
    Comment = "Training pipeline with validation and metrics logging",
    StartAt = "ValidateData",
    States = {
      ValidateData = {
        Type     = "Task",
        Resource = aws_lambda_function.validate.arn,
        Next     = "LogMetrics"
      },
      LogMetrics = {
        Type     = "Task",
        Resource = aws_lambda_function.log_metrics.arn,
        End      = true
      }
    }
  })
}


output "step_function_arn" {
  value       = aws_sfn_state_machine.train_pipeline.arn
  description = "ARN of the AWS Step Function"
}

output "lambda_validate_arn" {
  value       = aws_lambda_function.validate.arn
  description = "ARN of the validate Lambda function"
}

output "lambda_log_metrics_arn" {
  value       = aws_lambda_function.log_metrics.arn
  description = "ARN of the log_metrics Lambda function"
}
