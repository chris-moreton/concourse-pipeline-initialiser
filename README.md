# Concourse Pipeline Controller

## One Job To Rule Them All

This is a single-job Concourse pipeline that manages the pipelines of other services within the same Concourse instance.

It scans specified Git code repositories for updates to pipeline configurations. 

When an update is detected, the updated pipeline configuration is applied and the pipeline is triggered.

This allows developers working on the specified Git repositories to manage the pipeline without needing to install anything on their local machines.

It also enforces a consistency of pipeline configuration across projects.

## What Do You Want?

[To configure a Concourse pipeline in my project and have it managed by an existing pipeline controller].(#setup_pipeline_controller)

To set up a new controller on my own Concourse instance. Continue reading below.

## Setting up Your Own Instance of This Controller

### Prerequisites and How to Get Them

To use the opinionated pipeline initialiser, you will need:

* A Concourse Server
* A CredHub Server
* The Fly CLI
* The CredHub CLI

### Setup Concourse and CredHub

Please use [Control Tower](https://github.com/EngineerBetter/control-tower) to setup Concourse and CredHub.

### Setting the Pipeline Initialiser pipeline itself

To bootstrap the pipeline initialiser, you need to run:

    cd devops/concourse/
    CONCOURSE_SERVER=https://concourse.example.com CONCOURSE_ADMIN_PASSWORD=[YOUR_PASSWORD_HERE] ./init-me.sh
  
### Setting credentials

Set the following CredHub secrets

    /concourse/main/pipeline-initialiser/AWS_SECRET_ACCESS_KEY
    /concourse/main/pipeline-initialiser/AWS_ACCESS_KEY_ID
    /concourse/main/pipeline-initialiser/CONCOURSE_ADMIN_PASSWORD
    
The AWS key should be for the same user that was used to create the Concourse environment with Control Tower.
    
<a name="setup_pipeline_controller"/>
### Add Repositories to be Scanned

To cause a repository to be included in the scans, update the repositories.yml file and create a pull request.

Once the pull request is merged into master, your project will be scanned for new commits. 

When a new commit is found, the pipeline configuration will first be updated with any new changes and then the ***build*** job from the pipeline will be triggered.

    repos:
    - pipeline_name: directorzone-api
      deploy_key_credhub_location: /concourse/main/directorzone-api/GITHUB_DEPLOY_KEY
      uri: git@github.com:chris-moreton/directorzone-api
    - pipeline_name: directorzone-frontend
      deploy_key_credhub_location: /concourse/main/directorzone-frontend/GITHUB_DEPLOY_KEY
      uri: git@github.com:chris-moreton/directorzone-frontend
      
For each repository, you will need to add the correct deploy key to the CredHub location specified in the **deploy_key_credhub_location** field.
      
## Configure the Pipeline in your Projects

When you make commits to a repository that is registered with the pipeline controller, your repository will be scanned periodically for changes.

During a scan, the controller will look for a pipeline.yml file.

    devops
        concourse
            pipeline.yml
