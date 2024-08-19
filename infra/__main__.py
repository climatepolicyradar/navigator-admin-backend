"""An AWS Python Pulumi program"""

import pulumi
from admin_backend_app import create_admin_backend
from util.validate_aws_account import validate_aws_account, validate_stack_and_branch

validate_aws_account()
validate_stack_and_branch()

RUNTIME = "python3.9"
CONFIG = pulumi.Config()

backend_service = create_admin_backend()
