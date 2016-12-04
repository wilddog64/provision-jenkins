# -*- mode: ruby -*-
# vi: set ft=ruby :

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure("2") do |config|
  # The most common configuration options are documented and commented below.
  # For a complete reference, please see the online documentation at
  # https://docs.vagrantup.com.

  # automatically configure a private network
  config.vm.network :private_network, :auto_network => true
  config.vm.network :forwarded_port, guest:8080, host: 8080

  # Every Vagrant development environment requires a box. You can search for
  # boxes at https://atlas.hashicorp.com/search.
  config.vm.box = "hashicorp/precise64"

  config.vm.provision :ansible do | ansible |
    ansible.limit             = 'all'
    ansible.galaxy_roles_path = '..'
    # ansible.install_mode      = :pip
    # ansible.verbose           = 'vvv'
    ansible.playbook   = 'tests/playbook.yml'
    ansible.extra_vars = {
      'java_version' => 8,
      'jenkins_admin_password' => 'admin',
    }
  end
end