# Dreambox Python Library

This python library provide a common python functionality across
Dreambox Corp.  Currently, the library provide a limit support for AWS
through awscli command line utility.

## dreambox.aws.core

This is the core library one that provide for various aws functions within dreambox.aws namespace.
The library currently provide the following functions:

### aws_cmd

This is the most fundamental function in dreambox.aws namespace.  All other aws related
functions are wrapper around it.  The function call the `aws` command line tool via python
`subprocess` library and return result as a `json object`.

The function accepts the following parameters,

* cmd_cat: accept a valid `aws` commands.  For `aws` support commands refer to `aws help` for more
detail information.  This is a require parameter.
* profile: a profile define in ~/.aws/config.  For how to setup ~/.aws configuration file, refer to
[this document](http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html) for
more information. This is an optional parameter.  If no value is provided, the default value is
`dreambox`.
* region: this will accept a valid region present in `AWS service`. It is an optional.  If no value
provide, the default value will be `us-east-1`
* subcmd: a valid sub-command for a given `aws command`.  Refer to
[AWS Command Line Interface]( http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-using.html )
for detail.  This is a require parameter.
* **options: any valid option for a given `aws command sub-command ...`.
Refer to [AWS Command Line Interface]( http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-using.html )

*note: in python, this mean it will take a list of key/value pair as a function parameters. See
example below for what it means.*

Upon the success call, the function will return a json object back to caller.  It is up to calling function
how to parse the object to provide usable information.

#### function usages

* aws\_cmd(cmd\_cat='autoscaling', profile='dreambox', subcmd='describe-auto-scaling-groups', query='...')
* aws\_cmd(cmd\_cat='autoscaling', subcmd='describe-auto-scaling-groups', query='...')

will tranfer into this

    aws --profile dreambox --region us-east-1 autoscaling describe-auto-scaling-group --query ...

* aws\_cmd(cmd_cat='ec2', subcmd='describe-instances', instance_ids='...', query='...')

will be transfer to this

    aws --profile dreambox --region us-east-1 ec2 describe-instances --instance-ids ... --query ...

_note: '-' in the instance-id will crash with python keyword (as this is a minus sign), so we have to
replace it with '\_'.  The function will replace it back with '-'. \_

### aws\_ec2cmd

This function will execute aws ec2 command category.  This function calls `aws_cmd` internally. It accepts
the following parameters:

* profile: a profile define in ~/.aws/config.  For how to setup ~/.aws configuration file, refer to
[this document](http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html) for
more information. This is an optional parameter.  If no value is provided, the default value is
`dreambox`.
* region: this will accept a valid region present in `AWS service`. It is an optional.  If no value
provide, the default value will be `us-east-1`
* subcmd: a valid sub-command for a given `aws command`.  Refer to
[AWS Command Line Interface]( http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-using.html )
for detail.  This is a require parameter.
* **options: any valid option for a given `aws command sub-command ...`.
Refer to [AWS Command Line Interface]( http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-using.html )

#### function usages

* aws_ec2cmd(ec2profile='dreambox', ec2region='us-east-1', subcmd='describe-instances')
* aws_ec2cmd('dreambox', 'us-east-1', 'describe-instances')

The above functions call will transfer into this,

    aws --profile dreambox --region us-east-1 describe-instances

* aws_ec2cmd('dreambox', 'us-east-1', 'describe-instances', instance_id='...', query='...')

The above function call will transfer into this,

    aws --profile dreambox --region us-east-1 describe-instances --instance-id ... --query ...

### aws_asgcmd
This function takes in charge of executing `aws autoscaling` command groups.  The function accepts the
following parameters,

* profile: a profile define in ~/.aws/config.  For how to setup ~/.aws configuration file, refer to
[this document](http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html) for
more information. This is an optional parameter.  If no value is provided, the default value is
`dreambox`.
* region: this will accept a valid region present in `AWS service`. It is an optional.  If no value
provide, the default value will be `us-east-1`
* subcmd: a valid sub-command for `aws autoscaling`.  Refer to
[AWS Command Line Interface]( http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-using.html )
for detail.  This is a require parameter.
* **options: any valid option for a given `aws command sub-command ...`.
Refer to [AWS Command Line Interface]( http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-using.html )

#### function usages

* aws_asgcmd(ec2profile='dreambox', ec2region='us-east-1', 'describe-auto-scaling-groups')
* aws_asgcmd('dreambox', 'us-east-1', 'describe-auto-scaling-groups')

The above function statements will transfer into this,

    aws --profile dreambox --region us-east-1 describe-auto-scaling-groups

* aws_asgcmd('dreambox', 'us-east-1', 'describe-auto-scaling-groups' query='...')

The above function statement will transfer into this,

    aws --profile dreambox --region us-east-1 describe-auto-scaling-groups

## dreambox.aws.asg

This namespace provides functionality to manage `AWS Auto Scaling Group`. It provides the following functions.
It dpends on the dreambox.aws.core for some basic operations.

### get\_all\_asgs
This function return all the `auto scaling groups` define in a given `aws region`.  The function accepts the following
parameters:

* profile: a profile define in ~/.aws/config.  For how to setup ~/.aws configuration file, refer to
[this document](http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html) for
more information. This is an optional parameter.  If no value is provided, the default value is
`dreambox`.
* region: this will accept a valid region present in `AWS service`. It is an optional.  If no value
provide, the default value will be `us-east-1`
* **options: any valid option for a given `aws command sub-command ...`.

#### function usages

* get\_all\_asgs(ec2profile='dreambox', ec2region='us-east-1')
* get\_all\_asgs()

The above call will transfer to this `aws` command,

    aws --profile dreambox --region us-east-1 autoscaling auto-scaling-groups

* get\_all\_asgs(query='...')

The above call will transfer into,

    aws --profile dreambox --region us-east-1 autoscaling auto-scaling-groups --query '...'
