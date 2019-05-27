provider "credhub" {
  credhub_server = "https://${var.credhub_host}:8844/"
  client_id = "${var.credhub_client_id}"
  client_secret = "${var.credhub_client_secret}"
  skip_ssl_validation = true
}

provider "aws" {
  access_key = "${data.credhub_value.aws_terraform_access_key_id.value}"
  secret_key = "${data.credhub_value.aws_terraform_secret_access_key.value}"
  region = "eu-west-2"
}