# Jenkins
This role will download, configure, and start jenkins service. The role supports the these
two OS families, `RedHat` and `Debian`

# Requirements
To run test in Vagrant, you have to edit ```/etc/hosts``` file and set 127.0.0.1 to localhost.pd.local

# Role Variables
The variables in this role has two categories.

## OS Families Specific Variables
OS families specific variables define how to setup a
jenkins repo, and where to store jenkins environment file
for a particular OS family. They are defined in the 
vars directory under the root. Currently, `jenkins` role
support two OS families, `Debian` and `RedHat`. The variables are,

* jenkins_repo_key_url - a url that contains jenkin repo key
* jenkins_repo_url - a jekins repo url
* jenkins_ini_file - a jenkins initialize file

## Jenkins Variables
These variables are not OS specific ones but for jenkins itself.

* jenkins_connection_delay
* jenkins_connection_retries
* jenkins_hostname - a host name for the jenkins service. Default is `localhost`
* jenkins_http_port - jenkins endpoint port. Default value is 8080
* jenkins_plugins - what jenkins plugins need to be installed
* jenkins_admin_user - admin user for jenkins
* jenkins_admin_password - admin password
* jenkins_home - jenkins home directory. The default value is set to `/var/lib/jenkins`
* jenkins_jar_location - where jenkins-cli.jar store. The default value is `/opt/jenkins-cli.jar`
* jenkins_update_center_json_url - where to download update-center.json. The default value is `https://updates.jenkins-ci.org/update-center.json`

## GitSCM configuration
The two variables below are used to configure `git comitter` info

* jenkins_git_cmmiter_name - a name for the committer
* jenkins_git_commiter_email - an email address for the comitter

## scm-sync-configuration variables
This role will pre-install [SCM Sync configuration jenkins plugin](https://wiki.jenkins-ci.org/display/JENKINS/SCM+Sync+configuration+plugin), and the following are variables related to it,

* jenkins_github_url - this is an url that `scm-sync-configuration` can use to sync the configuration over. _Note_, the repo must exist for it.
* jenkins_sync_repo_empty - a boolean variable to tell `provision-jenkins` to configure the plugin.

## Plugins Install At Jenkins Initial Setup Time

* jenkins_default_plugins - this variable is a hash that contains a number of plugins will be installed during the jenkins configuration times. The hash contains the following `jenkins plugins`

	* ssh-credentials - this plugin is used to store ssh private key and passphrase
	* icon-shim - some plugins such as ssh-credentials depends on it to work
	* github - a plugin for interact with github.com
	* scm-sync-configuraion - a plugin backup jenkins configuration and sync with github
	* matrix-auth - a plugin this role uses to configure system security
	* build-token-root - a plugin that allow remote job execution
    * credentials - a credetial store
    * envinject - an environment variables inject plugin
    * github - a github plugin
    * greenballs
    * icon-shim
    * jobConfigHistory
    * matrix-auth
    * nodelabelparameter
    * publish-over-ssh
    * scm-sync-configuration
    * ssh-agent
    * ssh-credentials
    * ssh-slaves
    * workflow-aggregator
    * workflow-cps
    * workflow-job
    * workflow-multibranch
    * mesos
    * dashboard-view
    * matrixtieparent
    * excludeMatrixParent
    * configurationslicing

## Jenkins github management variables
The `provision-jenkins` role use `scm-sync-configuration` plugin to backup systemwise configuration. In order for this plugin to work effectively, these following variables need to be set

* jenkins_enable_github_repo - a boolean variable that tells `provision-jenkins` should create github repo or not. Default is `false`
* jenkins_github_org - the orgnization that this repo will be associated with
* jenkins_github_repo - a repo will be created under the `jenkins_github_org`
* jenkins_github_api_token - an OAuth token that allow `provision-jenkins` role to manage `repos` in github.com.You will have to first create an account and generate an `api token` that has the following permissions,

  * repo:status, repo_deployment, and public_repo
  * admin:public_key, write:public_key, and read:public_key
  * delete_repo

  The `github api token` should be treated as a sensitivity information. It should not be stored as a plain text. We strongly suggest to encrypt this information via `ansible-vault` for better a secunirityd.

Note: the value set for `jenkins_admin_password` is for testing only. For production use, you should move this setting to `ansible-vault`

# Dependencies

If you want `jenkins` to run with standard `Oracle Java`, you will have to include `provision-oracle-java` role,and set `oracle_java_version` variable.
This role also includes [ansible-install-python-pip](https://github.com/wilddog64/ansible-install-python-pip) to install `pip` and update it.

# Example Playbook

    ---
    - hosts: all
      gather_facts: no
      become: yes

	  vars:
        oracle_java_version: 8
        sshkey_passphrase: "{{ vault_sshkey_passphrase }}"
        jenkins_admin_password: "{{ vault_jenkins_admin_password }}"
        jenkins_git_commiter_name: your-deployer
        jenkins_git_commiter_email: your-deployer@your-org
        jenkins_github_url: git@github:wilddog64/jenkins-scm.git
        jenkins_sync_repo_empty: 1

      roles:
	    - provision-oracle-java
        - provision-jenkins

The above example `playbook` will provision a node with

* An `Oracle Java 8`
* An ssh private key with passphrase
* A proper username and email for a `git commiter`
* A git repo url for `scm-sync-configuration` jenkins plugin

The role has a task that will collect facts. So we turn off `gather_facts` at the playbook level
