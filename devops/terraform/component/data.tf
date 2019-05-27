data "credhub_value" "aws_terraform_access_key_id" {
  name = "/concourse/main/pipeline-controller/AWS_ACCESS_KEY_ID"
}

data "credhub_value" "aws_terraform_secret_access_key" {
  name = "/concourse/main/pipeline-controller/AWS_SECRET_ACCESS_KEY"
}

data "credhub_value" "db_port" {
  name = "/concourse/main/${var.product}-${var.component}/${var.environment}/DB_PORT"
}

data "credhub_value" "db_name" {
  name = "/concourse/main/${var.product}-${var.component}/${var.environment}/DB_NAME"
}

data "credhub_user" "db_user" {
  name = "/concourse/main/${var.product}-${var.component}/${var.environment}/DB_USER"
}

data "aws_vpc" "default" {
  default = true
}

data "aws_subnet_ids" "all" {
  vpc_id = "${data.aws_vpc.default.id}"
}

data "aws_region" "current" {}

data "aws_caller_identity" "current" {}