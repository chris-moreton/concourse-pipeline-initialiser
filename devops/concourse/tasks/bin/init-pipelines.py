import git
import yaml
import boto3
import os
import sys


def get_state(yaml_file):
    s3 = boto3.client('s3')
    tmp_file_location = "/tmp/temp.yml"
    try:
        s3.download_file(os.environ['STATE_BUCKET'], 'repositories.yml', tmp_file_location)
        state_file = open(tmp_file_location)
        state_yaml_file = yaml.safe_load(state_file)
    except:
        print("Unable to download repository state file")
        state_yaml_file = {"repos": yaml_file["repos"]}
    return state_yaml_file


def get_repos():
    repo_yml_filename = "repositories.yml"
    system_call("cp ../../../../" + repo_yml_filename + " .")
    f = open(repo_yml_filename)
    yaml_file = yaml.safe_load(f)
    return yaml_file


def get_teams():
    yml_filename = "teams.yml"
    system_call("cp ../../../../" + yml_filename + " .")
    f = open(yml_filename)
    yaml_file = yaml.safe_load(f)
    return yaml_file["teams"]


def load_yaml_file(filename):
    f = open(filename)
    return yaml.safe_load(f)


def merge_yaml_files(file1, file2):
    y1 = load_yaml_file(file1)
    y2 = load_yaml_file(file2)
    for y1Key in y1.keys():
        if y1Key in y2.keys():
            print("Merging key '" + y1Key + "' from custom pipeline into core pipeline")
            for y1Item in y1[y1Key]:
                y2[y1Key].append(y1Item)
        else:
            print("Adding key '" + y1Key + "' to core pipeline")
            y2[y1Key] = y1[y1Key]

    return yaml.dump(y2)


def get_state_repo_revisions():
    state_yaml_file = get_state(yaml_file)
    state_repo_revisions = {}
    for state_repo in state_yaml_file["repos"]:
        previous_head_revision = ""
        if "head_revision" in state_repo.keys():
            previous_head_revision = state_repo["head_revision"]
        state_repo_revisions[state_repo["pipeline_name"]] = previous_head_revision
    return state_repo_revisions


def save_state(yaml_file):
    s3 = boto3.client('s3')
    tmp_file_location = "/tmp/temp.yml"
    stream = open(tmp_file_location, "w")
    yaml.dump(yaml_file, stream)
    print("Saving state")
    with open(tmp_file_location, "rb") as f:
        s3.upload_fileobj(f, os.environ['STATE_BUCKET'], "repositories.yml")


def system_call(call_string):
    print("Running command: " + call_string)
    return_code = os.system(call_string)
    print("Exit code was: " + str(return_code))
    if return_code != 0:
        exit(1)


def get_project_type(repo):
    return repo["project_type"]


def login_to_team(team_name):
    system_call("fly -t netsensia-concourse login -n " + team_name + " --insecure --concourse-url https://" + sys.argv[
        1] + " -u admin -p " + sys.argv[2])


def initialise_pipeline(repo):
    pipeline_name = repo["pipeline_name"]
    project_type = get_project_type(repo)
    filename = "pipeline.yml"
    pipeline_config = "/tmp/" + pipeline_name + "/devops/concourse/" + filename
    merged_config = "/tmp/merged.yml"
    if repo["pipeline_type"] == "minimal":
        if os.path.isfile(pipeline_config):
            merged_pipeline_config = pipeline_config
        else:
            print(pipeline_config + " not found and no core config for minimal pipeline type.")
            exit(1)
    else:
        core_config = "../../external-" + repo["pipeline_type"] + ".yml"
        core_config_copy = "../../external-" + repo["pipeline_type"] + "-copy.yml"
        system_call("cp " + core_config + " " + core_config_copy)
        print("Project Type is " + project_type)
        system_call("sed -i s/PROJECT_TYPE/" + project_type + "/g " + core_config_copy)
        if os.path.isfile(pipeline_config):
            print("Merging external and custom pipeline jobs")
            merged = merge_yaml_files(pipeline_config, core_config_copy)
            print(merged)
            f = open(merged_config, "w")
            f.write(merged)
            f.close()
            merged_pipeline_config = merged_config
        else:
            merged_pipeline_config = core_config_copy
            print("No " + filename + " found.")

    team_name = pipeline_name.split("-")[0];
    pipeline_shortname = pipeline_name.split("-")[1];
    print("Updating pipeline " + pipeline_name + "...")
    login_to_team(team_name)

    system_call(
        "fly --target netsensia-concourse set-pipeline --non-interactive -c " + merged_pipeline_config + " -p " + pipeline_shortname
    )


def get_deploy_key(repo):


    print("Getting deploy key from CredHub...")

    if 'PYCHARM_HOSTED' in os.environ.keys() and os.environ['PYCHARM_HOSTED'] == "1":
        deploy_key_file = "/tmp/id_rsa"
    else:
        deploy_key_file = "/root/.ssh/id_rsa"

    prepare_deploy_key(deploy_key_file, repo)


def prepare_deploy_key(deploy_key_file, repo):
    parts = repo["pipeline_name"].split("-")
    print("Overwriting deploy key at " + deploy_key_file)
    sed = "sed -e 's/\(KEY-----\)\s/\\1\\n/g; s/\s\(-----END\)/\\n\\1/g' | sed -e '2s/\s\+/\\n/g'"
    system_call("credhub get -q -n " + "/concourse/" + parts[0] + "/" + parts[1] + "/GITHUB_DEPLOY_KEY" + " -k private_key | " + sed + " > " + deploy_key_file)
    system_call("chmod 600 ~/.ssh/id_rsa")


def set_component_and_product(pipeline_name):
    parts = pipeline_name.split("-")
    system_call("credhub set -n concourse/" + parts[0] + "/" + parts[1] + "/PRODUCT --type value --value " + parts[0])
    system_call("credhub set -n concourse/" + parts[0] + "/" + parts[1] + "/COMPONENT --type value --value " + parts[1])


def clone_repository(repo):
    os.system("ssh -o \"StrictHostKeyChecking=no\" " + repo["git_host"])
    system_call("rm -rf /tmp/" + repo["pipeline_name"])
    clone_dir = "/tmp/" + repo["pipeline_name"]
    cmd = "git clone -b " + repo["branch"] + " --single-branch " + repo["git_host"] + ":" + repo["git_org"] + "/" + repo["pipeline_name"] + " " + clone_dir
    print (cmd)
    system_call(cmd)
    return clone_dir


def get_current_head_revision(repo):
    get_deploy_key(repo)
    repo_object = git.Repo(clone_repository(repo))
    return repo_object.head.commit.name_rev.split()[0]


def get_previous_head_revision(repo):
    state_repo_revisions = get_state_repo_revisions()
    if repo["pipeline_name"] in state_repo_revisions.keys():
        return state_repo_revisions[repo["pipeline_name"]]
    else:
        return ""


def process_repositories(yaml_file):
    for repo in yaml_file["repos"]:

        print("Branch for " + repo["pipeline_name"] + " is " + repo["branch"])

        set_component_and_product(repo["pipeline_name"])

        current_head_revision = get_current_head_revision(repo)

        if current_head_revision == get_previous_head_revision(repo):
            print("Setting pipeline...")
            initialise_pipeline(repo)
        else:
            initialise_pipeline(repo)
            print("Triggering build job...")
            team_name = repo["pipeline_name"].split("-")[0];
            pipeline_shortname = repo["pipeline_name"].split("-")[1];
            system_call("fly --target netsensia-concourse trigger-job -j " + pipeline_shortname + "/" + "build")

        repo["head_revision"] = current_head_revision


def set_teams():
    teams = get_teams()
    for team in teams:
        print("Setting team: " + team["name"])
        tmp_file_location = "/tmp/config.yml"
        stream = open(tmp_file_location, "w")
        yaml.dump(team["config"], stream)
        system_call("fly -t netsensia-concourse set-team --non-interactive -n " + team["name"] + " --config /tmp/config.yml")


yaml_file = get_repos()
set_teams()
process_repositories(yaml_file)

save_state(yaml_file)
