provider "credhub" {
  credhub_server = "https://${var.credhub_host}:8844/"
  client_id = "${var.credhub_client_id}"
  client_secret = "${var.credhub_client_secret}"
  skip_ssl_validation = true
}

provider "aws" {
  access_key = "${var.aws_terraform_access_key_id}"
  secret_key = "${var.aws_terraform_secret_access_key}"
  region = "eu-west-2"
}

provider "aws" {
  alias = "us"
  access_key = "${var.aws_terraform_access_key_id}"
  secret_key = "${var.aws_terraform_secret_access_key}"
  region = "us-east-1"
}

provider "cloudfoundry" {
  api_url = "https://api.run.pivotal.io"
  user = "${var.cloudfoundry_org_owner_username}"
  password = "${var.cloudfoundry_org_owner_password}"
  skip_ssl_validation = true
}

provider "cloudfoundry" {
  alias = "ibm"
  api_url = "https://api.run.pivotal.io"
  user = "${var.cloudfoundry_ibm_org_owner_username}"
  password = "${var.cloudfoundry_ibm_org_owner_password}"
  skip_ssl_validation = true
}
