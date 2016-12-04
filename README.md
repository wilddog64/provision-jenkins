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

## General Variables
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

Note: the value set for `jenkins_admin_password` is for testing only. For production use, you should move this setting to `ansible-vault`

# Dependencies

There's no dependencies for this role.

# Example Playbook

    ---
    - hosts: all
      gather_facts: no
      become: yes
      roles:
        - jenkins

The role has a task that will collect facts. So we turn off `gather_facts` at the playbook level
