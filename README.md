# Jenkins
This role will download, configure, and start jenkins service. The role supports the these
two OS families, `RedHat` and `Debian`

# Requirements

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
* jenkins_java_args - options passes to java for start up. By default, this set to `-Djava.awt.headless=true -Djenkins.install.runSetupWizard=false` to by pass jenkins setup wizard
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

Note: the value set for `jenkins_admin_password` is for testing only. For production use, you should move this setting to `ansible-vault`

# Dependencies

If you want `jenkins` to run with standard `Oracle Java`, you will have to include `provision-oracle-java` role,and set `oracle_java_version` variable.

# Example Playbook

    ---
    - hosts: all
      gather_facts: no
      become: yes

	  vars:
        oracle_java_version: 8
        sshkey_passphrase: "{{ vault_sshkey_passphrase }}"
        jenkins_admin_password: "{{ vault_jenkins_admin_password }}"
        jenkins_git_commiter_name: ec2-deployer
        jenkins_git_commiter_email: operations@dreambox.com
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
