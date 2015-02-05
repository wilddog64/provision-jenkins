from littlechef import chef
import json
import subprocess
import os
import pprint
from funcy import *
from funcy.debug import *
from funcy.strings import *
import re
from itertools import *


# littlechef plugin entry: execute.  This method has to
# be always implemented in order for littlechef to execute this
# particular pluing
def execute(node):
    """
    get_ec2_inventory plugin will query ec2 autoscaling group to get all the
    instances hostname back
    """

    pp = pprint.PrettyPrinter(indent=3)
    current_directory = os.path.dirname(os.path.realpath(__file__))
    print "script executed: %s and current script directory is: %s" % \
        (__file__, current_directory)
    # aws_ec2cmd('dreambox', 'us-east-1', 'describe-instances',
    #         query='Reservations[].Instances[].[PublicDnsName,KeyName]')
    asg_query='AutoScalingGroups[*].[Tags[?Key==`Name`].Value,Instances[].InstanceId][]'
    result = get_all_play_asgs(ec2profile='dreambox',
                           ec2region='us-east-1',
                           env='production',
                           query=asg_query)
    print 'result from get_all_play_asgs'
    print '============================'
    pp.pprint(result)
    print 'end of get_all_play_asgs'
    print '============================'
    print

    print 'result from get_only_play_asgs'
    print '=============================='
    result = get_only_play_asgs(query=asg_query)
    pp.pprint(result)
    print 'end of get_only_play_asgs'
    print

    print 'result from get_ec2_instances_hostnames_from_asg_groups'
    print '======================================================='
    results = get_ec2_instances_hostnames_from_asg_groups(asg_group=result)
    pp.pprint(results)
    print 'end of get_ec2_instances_hostnames_from_asg_groups'
    print '=================================================='
    print

# base function for all other aws command line function.  this function
# accepts 5 parameters,
#
#   cmd_cat: is a aws command category. this can be ec2, autoscaling ...
#   profile: a profile that aws command will reference
#   region: which region aws is going to tackle
#   subcmd: a sub command for aws command category
#   **options: is a dict parameters that can pass to this particular
#              sub-command
def aws_cmd(cmd_cat='',
            profile='dreambox',
            region='us-east-1',
            subcmd='',
            **options):

    cmd_opts = ''
    my_options = {}
    if options:
        cmd_opts = ''
        for k, v in options.items():
            if '_' in k:
                k = re.sub('_', '-', k)
                print 'option key {}'.format(k)
                my_options[k] = v
            else:
                my_options[k] = v
        cmd_opts = ' '.join(["--{} {}".format(k, v)
                             for k, v in my_options.items()])
    aws_command = "aws --profile {} --region {} {} {} {}".format(profile,
             region, cmd_cat, subcmd, cmd_opts)
    print "prepare to execute %s " % aws_command
    cmd = aws_command.split(' ')
    proc = subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                            )
    result, error = proc.communicate()
    if not error:
        return json.loads(result)
    else:
        return error


# aws_ec2cmd is a function that will execute aws ec2 command category.  this
# function takes the following parameters,
#
#   ec2profile: profile defined in ~/.aws/config
#   ec2region: a region this function intend to work
#   subcmd: a sub-command that apply to aws ec2 command
#   **options: a list of command options that are applicable to a given
#     sub-command
#
# a json object will return upon a successful call
def aws_ec2cmd(
               ec2profile='dreambox',
               ec2region='us-east-1',
               subcmd='',
               **options):
    return aws_cmd('ec2',
            ec2profile,
            ec2region,
            subcmd,
            **options)


# aws_asgcmd is a function that execute aws autoscaling command.  this
# function takes 5 parameters,
#
#  aws_profile: profile define under ~/.aws/config
#  aws_region: an aws region to work with
#  asg_sugcmd: a sub-command applicable to autoscaling
#  **asg_options: a list of acceptable options to autoscaling sub-command
#
# aws_asgcmd will return a valid json object back to caller upon successful
# call
def aws_asgcmd(aws_profile='dreambox',
               aws_region='us-east-1',
               asg_subcmd=None,
               **asg_options):
    return aws_cmd(cmd_cat='autoscaling',
            profile=aws_profile,
            region=aws_region,
            subcmd=asg_subcmd,
            **asg_options)


# get_all_asgs is a function that will return all the ASG defined for
# a given region for AWS.  The function takes the following parameters,
#
#   ec2profile: a n ec2 profile defined under ~/.aws/config
#   ec2region: a valid region defined by AWS service
#   env: which envirnoment we are talking about. set to production by default
#   **options: a list of options that applying to
#              autoscaling describe-auto-scaling-groups
#
# this function will return a list of hashes upon a successful call
def get_all_asgs(ec2profile='dreambox',
                 ec2region='us-east-1',
                 **options):
    return aws_asgcmd(aws_profile=ec2profile,
                      aws_region=ec2region,
                      asg_subcmd='describe-auto-scaling-groups',
                      **options)

# get_play_asgs function will get all the play machine instances and store them
#   in a list of hashes.  this function takes the following parameters,
#
#   ec2profile: an ec2 profile stores in ~/.aws/config
#   ec2region: a region we are working on
#   env: environment we are looking for
#   **options: a list of options that can be accepted by
#     autoscaling describe-auto-scaling-groups
def get_all_play_asgs(ec2profile='dreambox',
                      ec2region='us-east-1',
                      env='production',
                      **options):
    hashes = make_hash_of_hashes(get_all_asgs(ec2profile, ec2region, **options))
    result = {}
    regex_pattern = r"{0}-(:?play_*|product_admin)".format(env)
    print "compiling regex pattern: {0}".format(regex_pattern)
    re_match = re.compile(regex_pattern, re.I)
    for k, v in hashes.items():
        if re_match.match(k) and '-db-' not in k:
            result[k.lower()] = v

    return result


# get_only_play_asgs will return all the play asg except _corn_ or _admin with
# the group names. this function accepts the following parameters,
#
#  ec2profile: a profile that is defined under ~/.aws/config
#  ec2region: region in AWS this function works on
#  env: what environment we are looking for
#  **options: a list of command line options that are applicable to
#     autoscaling describe-auto-scaling-groups
def get_only_play_asgs(ec2profile='dreambox',
                       ec2region='us-east-1',
                       env='production',
                       **options):
    all_play_asgs = get_all_play_asgs(ec2profile, ec2region, env, **options)
    result = {}
    for k, v in all_play_asgs.items():
        if '_cron_' not in k.lower() and '_admin' not in k.lower():
            result[k] = v
    return result

# make_hash_of_hashes will make an array of hashes from a given list by these
# steps,
#
#   1. create a pairwise list of tuples
#   2. transfer turple into a list
#   3. create a hash where key is the first element, and value is the reset
#   4. append hash to a list
#
# the function takes the following parameters,
#
#   my_list: a valid python list
#
# return a list of hashes upon a succesful call
def make_hash_of_hashes(my_list):
    turple = zip(my_list[::2], my_list[1::2])
    result = {}
    for item in turple:
        items = list(item)
        result[items[0][0]] = items[1]
    return result


# get_ec2_instances_hostnames_from_asg_groups will get instance hostnames from
# a given ASG group.  This function takes the following parameters,
#
#   ec2profile is profile defines in ~/.aws/config
#   ec2region
def get_ec2_instances_hostnames_from_asg_groups(ec2profile='dreambox',
                                                ec2region='us-east-1',
                                                asg_group={},
                                                **options):
    pp = pprint.PrettyPrinter(indent=3)
    info_query='Reservations[].[Instances[].[PublicDnsName,KeyName]][][]'
    results = []
    for k, v in asg_group.items():
        if v:
            ids = str_join(' ', v)
            result = aws_ec2cmd(ec2profile,
                                ec2region,
                                subcmd='describe-instances',
                                instance_ids=ids,
                                query=info_query)
            results.append(result)
    return results
