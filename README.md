# Concourse Pipeline Initialiser

NOTE: This README file is a work in progress. Check the last commit time to discover if I'm still updating it regularly :)

This is a Concourse pipeline that scans specified Git code repositories for updates to pipeline configurations. When an update is detected, the new pipeline configuration is applied and the first job in the pipeline is triggered.

This allows developers working on the specified Git repositories to manage the pipeline without needing to install anything on their local machines.

It also enforeces a consistency of pipeline configuration across projects.

## Prerequisites and How to Get Them

To use the opinionated pipeline initialiser, you will need:

* A Concourse Server
* A CredHub Server
* The Fly CLI
* The CredHub CLI

### Setup Concourse and CredHub

I recommend using [Control Tower](https://github.com/EngineerBetter/control-tower) to setup Concourse and CredHub.

### Setting the Pipeline Initialiser pipeline itself

To bootstrap the pipeline initialiser, you need to run:

    CONCOURSE_SERVER=https://concourse.example.com CONCOURSE_ADMIN_PASSWORD=[YOUR_PASSWORD_HERE] sh devops/concourse/init-me.sh
  
### Setting credentials

Set the following CredHub secrets

    /concourse/main/pipeline-initialiser/AWS_SECRET_ACCESS_KEY
    /concourse/main/pipeline-initialiser/AWS_ACCESS_KEY_ID
    /concourse/main/pipeline-initialiser/CONCOURSE_ADMIN_PASSWORD
    
### Add Repositories to be Scanned

To cause a repository to be included in the scans, update the repositories.yml file and create a pull request. Once the pull request
is merged into master, your project will be scanned for new commits. When a new commit is found, the pipeline configuration will first
be updated with any new changes and then the ***build*** job from the pipeline will be triggered.

    repos:
    - deploy_key_credhub_location: /concourse/main/directorzone-api/GITHUB_DEPLOY_KEY
      pipeline_name: directorzone-api
      uri: git@github.com:chris-moreton/directorzone-api
    - deploy_key_credhub_location: /concourse/main/directorzone-frontend/GITHUB_DEPLOY_KEY
      pipeline_name: directorzone-frontend
      uri: git@github.com:chris-moreton/directorzone-frontend
      
For each repository, you will need to add the correct deploy key to the CredHub location specified in the **deploy_key_credhub_location** field.
      
## Configure the Pipeline in your Projects

## Building Infrastructure

All the infrastructure required to run your services should be created in the pipeline using Terraform definitions.

### Storing Secrets Generated by Terraform

When Terraform generates a secret as part of a resource, such as an AWS access key for an IAM user, it will store that secret in its
state file in S3. To avoid storing the bare secret, take the option to encrypt.

Here is an example of creating an AWS user along with an access key:

    resource "aws_iam_user" "s3_user" {
      name = "${var.product}-${var.component}-s3-user"
    }
    
    resource "aws_iam_access_key" "s3_user_iam_access_key" {
      user    = "${aws_iam_user.s3_user.name}"
      pgp_key = "keybase:${data.credhub_value.keybase_user.value}"
      depends_on = ["aws_iam_user.s3_user"]
    }
    
    resource "credhub_generic" "s3_user_iam_access_key_id" {
      depends_on = ["aws_iam_access_key.s3_user_iam_access_key"]
      type = "value"
      name = "/concourse/main/${var.product}-${var.component}/S3_BUCKET_ACCESS_KEY_ID"
      data_value = "${aws_iam_access_key.s3_user_iam_access_key.id}"
    }
    
    resource "credhub_generic" "s3_user_iam_secret_access_key_encrypted" {
      depends_on = ["aws_iam_access_key.s3_user_iam_access_key"]
      type = "value"
      name = "/concourse/main/${var.product}-${var.component}/S3_BUCKET_SECRET_ACCESS_KEY_ENCRYPTED"
      data_value = "${aws_iam_access_key.s3_user_iam_access_key.encrypted_secret}"
    }

If you have the Keybase and Credhub CLIs installed, you can decrypt the generated value and store it bare within CredHub with a command
such as:

    credhub set -n concourse/main/directorzone-api/S3_BUCKET_SECRET_ACCESS_KEY --type value --value \
    `credhub get -qn concourse/main/directorzone-api/S3_BUCKET_SECRET_ACCESS_KEY_ENCRYPTED \
    | \base64 --decode | keybase pgp decrypt`