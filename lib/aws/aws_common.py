from boto.ec2.autoscale.tag import Tag
from boto.exception import BotoServerError
import boto.utils
import requests
import os
import datetime
import itertools
import subprocess
import logging
import json
import sys
import time
from fabfile import *
from fabric.api import execute as fab_execute
from fabric.state import env
import zipfile
import StringIO


class DeployException(Exception):
    pass

def set_up_logging():
    global logger
    logger = logging.getLogger(__name__)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.setLevel(logging.INFO)
    return logger


def set_mgmt_load_sensu_stash(chef_environment, timeout_val):
    try:
        prod_sensu_url = 'https://production-sensu-service.dreambox.com:4567'
        resp = requests.get("%s/clients" % prod_sensu_url)
        # west mgmt node is not in sensu but needs to be for this to work in the west
        mgmt_host = str([ e["name"] for e in resp.json() if e["name"].startswith("mgmt") and e["chef"]["environment"] == "production" ][0])
        # need to detect region if used in stage as well as mod the homepage target
        try:
            for check in [ 'check_load']:
                payload = '{"path": "silence/%s/%s", "expire":%d, "content":{"reason":"Silencing for %s deployment.","timestamp":%d}}' % (mgmt_host, check, timeout_val, chef_environment, int(time.time()))
                resp = requests.post("%s/stashes" % prod_sensu_url, data=payload)
                logger.info('Downtime response for %s received: %s' % (check, resp))
        except Exception as e:
            logger.info('Downtime response for %s failed: %s' % (check, resp))
    except Exception as e:
        logger.info('Request to delete sensu checks on mgmt failed: %s' % e)
        resp = True
    return resp


def set_mgmt_sensu_stashes(chef_environment, timeout_val):
    try:
        prod_sensu_url = 'https://production-sensu-service.dreambox.com:4567'
        resp = requests.get("%s/clients" % prod_sensu_url)
        # west mgmt node is not in sensu but needs to be for this to work in the west
        mgmt_host = str([ e["name"] for e in resp.json() if e["name"].startswith("mgmt") and e["chef"]["environment"] == "production" ][0])
        # need to detect region if used in stage as well as mod the homepage target
        try:
            for check in [ 'check_homepage-%s-play' % chef_environment, 'check_load', 'check_active_ASGs-us-east-1', 'check_active_ASGs-us-west-2']:
                payload = '{"path": "silence/%s/%s", "expire":%d, "content":{"reason":"Silencing for %s deployment.","timestamp":%d}}' % (mgmt_host, check, timeout_val, chef_environment, int(time.time()))
                resp = requests.post("%s/stashes" % prod_sensu_url, data=payload)
                logger.info('Downtime response for %s received: %s' % (check, resp))
        except Exception as e:
            logger.info('Downtime response for %s failed: %s' % (check, resp))
    except Exception as e:
        logger.info('Request to delete sensu checks on mgmt failed: %s' % e)
        resp = True
    return resp


def del_mgmt_sensu_stashes(chef_environment): # no longer used as we actually extend downtime on mgmt for an extra 15 mins after release
    try:
        prod_sensu_url = 'https://production-sensu-service.dreambox.com:4567'
        resp = requests.get("%s/clients" % prod_sensu_url)
        # west mgmt node is not in sensu but needs to be for this to work in the west
        mgmt_host = str([ e["name"] for e in resp.json() if e["name"].startswith("mgmt") and e["chef"]["environment"] == "production" ][0])
        # need to detect region if used in stage as well as mod the homepage target
        for check in [ 'check_homepage-%s-play' % chef_environment, 'check_load', 'check_active_ASGs-us-east-1', 'check_active_ASGs-us-west-2' ]:
            resp = requests.delete("%s/stashes/silence/%s/%s" % (prod_sensu_url, mgmt_host, check))
            logger.info('Downtime response for %s received: %s' % (check, resp))
    except Exception as e:
        logger.info('Request to delete sensu checks on mgmt failed: %s' % e)
        resp = True
    return resp


def reload_product(instance_hostnames):
    fab_execute(product_reload, hosts=instance_hostnames)
    fab_execute(product_admin_reload, hosts=instance_hostnames)


def get_hostnames_from_reservations(reservations):
    instances = []
    for r in reservations:
        instances += r.instances
    instance_hostnames = [ i.public_dns_name for i in instances ]
    return instance_hostnames


def get_hostnames_from_instance_ids(instance_ids):
    if not instance_ids:
        return []
    region = get_region()
    ec2_conn = boto.ec2.connect_to_region(region)
    reservations = ec2_conn.get_all_instances(instance_ids)
    hostnames = get_hostnames_from_reservations(reservations)
    return hostnames


def get_as_groups(all_groups, env, app):
    return [ g for g in all_groups if [ t for t in g.tags if t.key == 'Name' and env+'-'+app in t.value.lower() and not '-db-' in t.value ] ]


def get_app_server_hosts(play_app_groups, env):
    return get_hostnames_from_instance_ids([ i.instance_id for i in list(itertools.chain(*[ g.instances for g in play_app_groups if [ t for t in g.tags if t.key == 'Name' and t.value == env + '-play' or t.value == env + '-play_highDemand' ] ])) ] )


def get_name_tag_value_from_id(instance_ids):
    if not instance_ids:
        return []
    region = get_region()
    ec2_conn = boto.ec2.connect_to_region(region)
    reservations = ec2_conn.get_all_instances(instance_ids)
    return [ r.instances[0].tags['Name'] for r in reservations ]


def get_region():
    try:
        region = boto.utils.get_instance_metadata(timeout=1, num_retries=2)['placement']['availability-zone'][:-1]
    except:
        region = 'us-east-1'
    return region

def get_api_script_host_from_asgs(asg_list):
    # try to grab a cron host first
    if [ g for g in asg_list if [ t for t in g.tags if t.key == 'Name' and ( t.value.endswith('api_worker') or t.value.endswith('Api_cron') ) ] ]:
        return get_hostnames_from_instance_ids([ g for g in asg_list if [ t for t in g.tags if t.key == 'Name' and ( t.value.endswith('api_worker') or t.value.endswith('Api_cron') ) ] ][-1].instances[0].instance_id)[0]
    # if not, use a random api host
    else:
        return get_hostnames_from_instance_ids(asg_list[-1].instances[0].instance_id)[0]


def get_play_script_host_from_asgs(asg_list):
    # try cron_standalone first
    if [ g for g in asg_list if [ t for t in g.tags if t.key == 'Name' and t.value.endswith('cron_standalone') ] ]:
        return get_hostnames_from_instance_ids([ g for g in asg_list if [ t for t in g.tags if t.key == 'Name' and t.value.endswith('cron_standalone') ] ][-1].instances[0].instance_id)[0]
    # try cron_worker second
    elif [ g for g in asg_list if [ t for t in g.tags if t.key == 'Name' and ( t.value.endswith('cron_worker') or t.value.endswith('play-worker') ) ] ]:
        return get_hostnames_from_instance_ids([ g for g in asg_list if [ t for t in g.tags if t.key == 'Name' and ( t.value.endswith('cron_worker') or t.value.endswith('play-worker') ) ] ][-1].instances[0].instance_id)[0]
    # a random play host last
    else:
        return get_hostnames_from_instance_ids(asg_list[-1].instances[0].instance_id)[0]


def newrelic_deploy_notification(app_name, revision):
    api_key = '4c778451f2e508e757cb5d6d183fe855148710a2'
    r = requests.post('https://api.newrelic.com/deployments.xml', headers={'x-api-key' : api_key}, data='deployment[app_name]=%s&deployment[revision]=%s' % (app_name, revision))
    return r.text


def is_galactus_deployed(stack):
    return 'yes' in [ p.value for p in stack.parameters if p.key == 'IncludeASG']


def get_tomcat_endpoint_user(chef_environment, service, endpoint_key, default_user):
    document = json.load(open(chef_environment_path(chef_environment)))
    if document['default_attributes'][service].has_key(endpoint_key) and document['default_attributes'][service][endpoint_key].has_key('username'):
        user = document['default_attributes'][service][endpoint_key]['username']
    else:
        user = default_user
    return user


def get_tomcat_endpoint_passwd(chef_environment, service, endpoint_key, default_pass):
    document = json.load(open(chef_environment_path(chef_environment)))
    if document['default_attributes'][service].has_key(endpoint_key) and document['default_attributes'][service][endpoint_key].has_key('password'):
        passwd = document['default_attributes'][service][endpoint_key]['password']
    else:
        passwd = default_pass
    return passwd


def check_tomcat_service_status(instance, user, passwd, version_endpoint):
    try:
        r = requests.get('http://' + instance + ':8080/' + version_endpoint, auth=(user, passwd), timeout=3)
        if r.status_code == 200:
            return r
        else:
            logger.info('Request to host %s failed. Trying again.' % instance)
            return False
    except Exception as e:
        logger.exception('Request to host %s failed with an exception: %s' % (instance, str(e)))
        return False


def get_tomcat_service_version_info(chef_environment, service):
    version_dict = {}
    s3_conn = boto.s3.connect_to_region('us-east-1') #NOTE: thus far we don't use the west but may need it
    document = json.load(open(chef_environment_path(chef_environment)))
    version_dict['type'] = document['default_attributes'][service]['version']['type']
    version_dict['number'] =  document['default_attributes'][service]['version']['number']
    if version_dict['type'] == 'snapshot':
        version_dict['timestamp'] =  document['default_attributes'][service]['version']['timestamp']
        if version_dict['timestamp'] == 'latest':
            if service == 'magneto':
                service = 'provision'
            bucket = s3_conn.get_bucket('dreambox-deployment-files')
            objects = bucket.list(prefix='Nexus/snapshots/com/dreambox/dbl-%s-main/%s-SNAPSHOT/' % (service, version_dict['number']))
            zip_keys = [ k.key for k in objects if k.key.endswith('.zip') ]
            zip_keys.sort()
            version_dict['timestamp'] = zip_keys[-1].split('.zip')[0].split('/')[-1].split('-', 4)[-1]
    return version_dict


def chef_environment_path(environment_name):
    #return '../chef/chef-environments/%s.json' % (environment_name) #XXX for testing locally
    return '%s/environments/%s.json' % (os.getenv('WORKSPACE'), environment_name)


def get_chef_environment_document(chef_environment):
    document = json.load(open(chef_environment_path(chef_environment)))
    return document


def get_product_revision(chef_environment):
    document = json.load(open(chef_environment_path(chef_environment)))
    if document['default_attributes']['product'].has_key('build_key'):
        return document['default_attributes']['product']['build_key'].replace('/','-')


def get_product_db(chef_environment):
    document = json.load(open(chef_environment_path(chef_environment)))
    return document['default_attributes']['product']['db']['product_production_host']


def get_api_revision(chef_environment):
    document = json.load(open(chef_environment_path(chef_environment)))
    return document['default_attributes']['api']['subversion']['revision']


def get_api_url(chef_environment):
    document = json.load(open(chef_environment_path(chef_environment)))
    return document['default_attributes']['api']['subversion']['url']


def get_lessons_revision(chef_environment):
    document = json.load(open(chef_environment_path(chef_environment)))
    return document['default_attributes']['lessons']['key'].replace('/','-')


def throttle_response(e):
    if e.error_code == 'Throttling':
        print('Pausing for AWS throttling...')
        time.sleep(1)
    else:
        print(str(e))
        sys.exit(1)


def update_chef_environment(environment_name):
    command = 'knife environment from file %s' % chef_environment_path(environment_name)
    subprocess.check_call(command.split())


def suspend_processes(autoscaling_group):
    try:
        # tag
        t = Tag(key='UpdateInProgress', value='true', resource_id=autoscaling_group.name)
        autoscaling_group.connection.create_or_update_tags([t])
        # suspend
        autoscaling_group.suspend_processes()
    except BotoServerError as e:
        throttle_response(e)
        suspend_processes(autoscaling_group)


def resume_processes(autoscaling_group):
    try:
        # resume
        autoscaling_group.resume_processes()
        # tag
        t = Tag(key='UpdateInProgress', value='false', resource_id=autoscaling_group.name)
        autoscaling_group.connection.create_or_update_tags([t])
    except BotoServerError as e:
        throttle_response(e)
        resume_processes(autoscaling_group)


def check_timeout(start_time, seconds):
    time_delta = datetime.datetime.now() - start_time
    elapsed_seconds = (time_delta.microseconds + (time_delta.seconds + time_delta.days * 24 * 3600) * 10**6) / 10**6

    if elapsed_seconds > seconds:
        raise DeployException('Timeout of %s seconds exceeded.' % seconds)
    else:
        return True


def get_autoscaling_group_object_dict(group_names_dict):
    '''
    Given a mapping of logical names to AWS group names, return a mapping of logical
    names to autoscaling group objects.
    '''
    region = get_region()
    as_conn = boto.ec2.autoscale.connect_to_region(region)
    all_groups = as_conn.get_all_groups([g for g in group_names_dict.values()])
    group_object_dict = {}
    for k in group_names_dict:
        for g in all_groups:
            if g.name == group_names_dict[k]:
                group_object_dict[k] = g
                continue
    return group_object_dict


def bool_filter(value):
    if value == 'false':
        return False
    elif value == 'true':
        return True
    else:
        return value


def get_implementation(file_name, build_key):
    try:
        z = zipfile.ZipFile(StringIO.StringIO(build_key.read()))
        ver_file = z.open(file_name+'/VERSION.TXT')
        contents = ver_file.readlines()
    except Exception as e:
        logger.error('Encountered an error: %s' % e)
        logger.error('This often indicates the key specified in the environment.json file does not exist as an available build in s3. Check the following location: %s' % build_key)
        sys.exit(1)
    return contents[1].split('"')[1]


# XXX collapse these to a general functions (get_json_value) to get environment value from 3 or 4 keys
def get_api_db_passwd(chef_environment):
    document = json.load(open(chef_environment_path(chef_environment)))
    if document['default_attributes']['api'].has_key('db') and document['default_attributes']['api']['db'].has_key('api_host'):
        return document['default_attributes']['api']['db']['api_host']
    else:
        return '%s-api-db.dreambox.com' % chef_environment


def get_api_db(chef_environment):
    document = json.load(open(chef_environment_path(chef_environment)))
    if document['default_attributes']['api'].has_key('db') and document['default_attributes']['api']['db'].has_key('api_host'):
        return document['default_attributes']['api']['db']['api_host']
    else:
        return '%s-api-db.dreambox.com' % chef_environment


def get_galactus_db_host(chef_environment):
    document = json.load(open(chef_environment_path(chef_environment)))
    if document['default_attributes']['galactus'].has_key('db') and document['default_attributes']['galactus']['db'].has_key('host'):
        print(document['default_attributes']['galactus']['db']['host'])
        return document['default_attributes']['galactus']['db']['host']
    else:
        return '%s-galactus-db.dreambox.com' % chef_environment


def get_galactus_db_user(chef_environment):
    document = json.load(open(chef_environment_path(chef_environment)))
    if document['default_attributes']['galactus'].has_key('db') and document['default_attributes']['galactus']['db'].has_key('username'):
        return document['default_attributes']['galactus']['db']['username']
    else:
        return 'galactus'


def get_galactus_db_passwd(chef_environment):
    document = json.load(open(chef_environment_path(chef_environment)))
    if document['default_attributes']['galactus'].has_key('db') and document['default_attributes']['galactus']['db'].has_key('password'):
        return document['default_attributes']['galactus']['db']['password']
    else:
        return 'worldeater'


def get_galactus_url(chef_environment):
    if chef_environment == 'production':
        url = 'galactus'
    else:
        url = chef_environment + '-galactus'
    return 'https://' + url + '.dreambox.com'


def get_play_asgs(as_conn, chef_environment):
    all_asgs = as_conn.get_all_groups()
    play_asgs = get_as_groups(all_asgs, chef_environment, 'play') + get_as_groups(all_asgs, chef_environment, 'product_admin') + get_as_groups(all_asgs, chef_environment, 'play_admin')
    only_play_asgs = list(set(play_asgs) - set([ g for g in play_asgs if [ t for t in g.tags if t.key == 'Name' and 'cron' in t.value or 'admin' in t.value ] ] ) )
    app_server_hosts = get_app_server_hosts(play_asgs, chef_environment)
    return (play_asgs, only_play_asgs, app_server_hosts)


def get_json_environment_values(chef_environment, value_locations):
    document = json.load(open(chef_environment_path(chef_environment)))
    version_dict = {}
    for k,v in value_locations.items():
        version_dict[k] = get_json_value(document, value_locations[k])
    if version_dict:
        return version_dict
    else:
        raise Exception('Location not found in the environment file!')


def get_json_value(document, value_location, base='default_attributes'):
    if len(value_location) == 1 and value_location[0] in document[base].keys():
        return document[base][value_location[0]]
    if len(value_location) == 2 and value_location[0] in document[base].keys() and value_location[1] in document[base][value_location[0]].keys():
        return document[base][value_location[0]][value_location[1]]
    elif len(value_location) == 3 and value_location[0] in document[base].keys() and value_location[1] in document[base][value_location[0]].keys() and value_location[2] in document[base][value_location[0]][value_location[1]].keys():
        return document[base][value_location[0]][value_location[1]][value_location[2]]
    else:
        raise Exception('Value could not be located in the doc %s' % str(value_location))


def set_json_environment_values(chef_environment, value_locations, desired_values_dict):
    document = json.load(open(chef_environment_path(chef_environment)))
    version_dict = {}
    for k,v in value_locations.items():
        document = set_json_value(document, value_locations[k], desired_values_dict[value_locations[k][-1]])
    json_file = open(chef_environment_path(chef_environment), "w+")
    json_file.write(json.dumps(document, sort_keys=True, indent=2, separators=(',', ': ')))
    return json_file.close()


def set_json_value(document, value_location, desired_val, base='default_attributes'):
    if len(value_location) == 1 and value_location[0] in document[base].keys():
        document[base][value_location[0]] = desired_val
    elif len(value_location) == 2 and value_location[0] in document[base].keys() and value_location[1] in document[base][value_location[0]].keys():
        document[base][value_location[0]][value_location[1]] = desired_val
    elif len(value_location) == 3 and value_location[0] in document[base].keys() and value_location[1] in document[base][value_location[0]].keys() and value_location[2] in document[base][value_location[0]][value_location[1]].keys():
        document[base][value_location[0]][value_location[1]][value_location[2]] = desired_val
    else:
        raise Exception('Could not replace value in json doc %s' % (str(value_location)))
    return document

def throwaway():
    return 'nada'
def get_instance_hostnames(autoscaling_group_obj):
    try:
        ec2_instances = autoscaling_group_obj.instances
        instance_hostnames = get_hostnames_from_instance_ids([i.instance_id for i in ec2_instances])
        logger.info('%s hosts identified in ASG %s: %s...' % (str(len(instance_hostnames)), autoscaling_group_obj.name, str(instance_hostnames)))
        return instance_hostnames
    except BotoServerError as e:
        throttle_response(e)
        get_instance_hostnames(autoscaling_group_obj)


def get_autoscaling_group_object(as_conn, environment_name, app_name):
    try:
        all_groups = as_conn.get_all_groups()
        return [g for g in all_groups if environment_name.lower() in g.name.lower() and app_name.lower() in g.name.lower()][0]
    except BotoServerError as e:
        throttle_response(e)
        get_autoscaling_group_obj(as_conn, environment_name, app_name)


def find_ami_by_filters(ec2_conn, virtualization_type, full_repo_releasever, chef_package_url=None, chef_environment=None, chef_role=None, app_versions=None, core_service_startup_md5=None):
    filters = {
        'image_type': 'machine',
        'architecture': 'x86_64',
        'state': 'available',
        'root_device_type': 'ebs',
        'hypervisor': 'xen',
        'image_type': 'machine',
        'virtualization_type': virtualization_type,
    }

    if app_versions:
        filters['tag:app_versions'] = app_versions
    if chef_role:
        filters['tag:chef_role'] = chef_role
    if chef_environment:
        filters['tag:chef_environment'] = chef_environment
    if chef_package_url:
        filters['tag:chef_package_url'] = chef_package_url
    if full_repo_releasever:
        filters['tag:full_repo_releasever'] = full_repo_releasever
    if core_service_startup_md5:
        filters['tag:core_service_startup_md5'] = core_service_startup_md5

    images = ec2_conn.get_all_images(filters=filters)

    owner = '642622324794'
    # print(filters)
    images = ec2_conn.get_all_images(owners=owner, filters=filters)
    return images


def get_app_versions(chef_environment, chef_role, json_doc=None):
    app_dict = get_all_apps_metadata()
    env_file_app_locations_list = [list(app_dict[k]['version_locations'].values()) for k in app_dict.keys() if chef_role in app_dict[k]['roles']]
    app_version_dict = {}
    for app in env_file_app_locations_list:
        for location in app:
            if json_doc:
                json_container = json.loads('{"default_attributes": {}}')
                json_container['default_attributes'] = json_doc
                app_version_dict['-'.join(location)] = get_json_value(json_container, location)
            else:
                app_version_dict['-'.join(location)] = get_json_value(get_chef_environment_document(chef_environment), location)
    return app_version_dict

def get_all_apps_metadata():
    app_dict = {
        'account': {
            'version_locations': {
                '/opt/account': ('account', 'version', 'number'), },  # ideally we could check ['magneto']['version']['type'] also
            'service': 'tomcat7',
            'roles': ['account'],
            },
        'api': {
            'version_locations': {
                '/home/mongrel/Api/': ('api', 'subversion', 'revision'), },  # also here it would be nice to test branch (if not move to s3)
            'service': 'api',
            'roles': ['PRODUCTION_api_cron_server', 'api_app', 'PRODUCTION_api_server', 'PRODUCTION_product_admin_server'],
        },
        'dreamboxcom': {
            'version_locations': {
                '/home/mongrel/DreamBoxCom/current': ('api', 'subversion', 'revision'), },
            'service': 'dreamboxcom',
            'roles': ['dreamboxcom_app', 'PRODUCTION_dreamboxcom_server'],
        },
        'galactus': {
            'version_locations': {
                '/opt/galactus': ('galactus', 'version', 'number'), },
            'service': 'tomcat7',
            'roles': ['galactus'],
        },
        'magneto': {
            'version_locations': {
                '/opt/provision': ('magneto', 'version', 'number'), },
            'service': 'tomcat7',
            'roles': ['magneto'],
        },
        'product': {
            'version_locations': {
                '/home/mongrel/Product/current': ('product', 'build_key'),
                '/home/mongrel/assets/lessons/current': ('lessons', 'key'),
            },
            'service': 'product',
            'roles': ['PRODUCTION_product_app_server', 'PRODUCTION_product_rpc_server', 'PRODUCTION_product_reports_server', 'play-admin', 'cron_worker', 'play_app', 'cron_standalone'],
        },
        'product_admin': {
            'version_locations': {
                '/home/mongrel/Product/current': ('product', 'build_key'), },  # lessons are unimportant on admin nodes
            'service': 'product_admin',
            'roles': ['PRODUCTION_product_app_server', 'PRODUCTION_product_rpc_server', 'PRODUCTION_product_reports_server', 'play-admin', 'cron_worker', 'play_app', 'cron_standalone'],
        },
    }
    return app_dict


def get_instance_hostnames_from_asg(asg):
   return get_hostnames_from_instance_ids([i.instance_id for i in asg.instances])

