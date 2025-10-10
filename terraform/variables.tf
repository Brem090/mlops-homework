variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "eu-north-1"
}

variable "lambda_runtime" {
  description = "Runtime environment for Lambda functions"
  type        = string
  default     = "python3.9"
}

variable "validate_function_name" {
  description = "Name of the Validate Lambda function"
  type        = string
  default     = "validate-fn"
}

variable "log_metrics_function_name" {
  description = "Name of the LogMetrics Lambda function"
  type        = string
  default     = "log-metrics-fn"
}

variable "lambda_role_name" {
  description = "IAM role name for Lambda execution"
  type        = string
  default     = "lambda_exec_role"
}

variable "step_role_name" {
  description = "IAM role name for Step Functions"
  type        = string
  default     = "stepfunction_role"
}

variable "state_machine_name" {
  description = "Name of the Step Function state machine"
  type        = string
  default     = "TrainModelPipeline"
}