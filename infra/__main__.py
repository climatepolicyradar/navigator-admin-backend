"""An AWS Python Pulumi program"""

import json

import pulumi
import pulumi_aws as aws
from admin_backend_app import create_admin_backend
from util.validate_aws_account import validate_aws_account, validate_stack_and_branch

validate_aws_account()
validate_stack_and_branch()

RUNTIME = "python3.9"
CONFIG = pulumi.Config()

backend_service = create_admin_backend()


stack = pulumi.get_stack()
account_id = aws.get_caller_identity().account_id


def protect_rds_instances(
    args: pulumi.ResourceTransformationArgs,
) -> pulumi.ResourceTransformationResult:
    if args.type_ == "aws:rds/instance:Instance":
        # Only set protect=True if it hasn't been explicitly set to False allowing overrides
        if args.opts.protect is not False:
            args.opts.protect = True

    return pulumi.ResourceTransformationResult(props=args.props, opts=args.opts)


pulumi.runtime.register_stack_transformation(protect_rds_instances)

# annoyingly the db_name wasn't set when provisioning staging
# and can't be changed post-launch, so we have to set it to nothing
rds_database = None if stack == "staging" else CONFIG.require("rds_database")
rds_username = CONFIG.require("rds_username")
db_subnet_group_name = CONFIG.require("db_subnet_group_name")
vpc_security_group_ids = [CONFIG.require("rds_vpc_security_group_id")]


rds_monitoring_role = aws.iam.Role(
    "rds_monitoring_role",
    assume_role_policy=json.dumps(
        {
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Effect": "Allow",
                    "Principal": {"Service": "monitoring.rds.amazonaws.com"},
                    "Sid": "",
                }
            ],
            "Version": "2012-10-17",
        }
    ),
    managed_policy_arns=[
        "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
    ],
    name="rds-monitoring-role",
    opts=pulumi.ResourceOptions(protect=True),
)

rds_kms_key = aws.kms.Key(
    "rds_kms_key",
    description="Default key that protects my RDS database volumes when no other key is defined",
    enable_key_rotation=True,
    policy=json.dumps(
        {
            "Id": "auto-rds-2",
            "Statement": [
                {
                    "Action": [
                        "kms:Encrypt",
                        "kms:Decrypt",
                        "kms:ReEncrypt*",
                        "kms:GenerateDataKey*",
                        "kms:CreateGrant",
                        "kms:ListGrants",
                        "kms:DescribeKey",
                    ],
                    "Condition": {
                        "StringEquals": {
                            "kms:CallerAccount": account_id,
                            "kms:ViaService": "rds.eu-west-1.amazonaws.com",
                        }
                    },
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Resource": "*",
                    "Sid": "Allow access through RDS for all principals in the account that are authorized to use RDS",
                },
                {
                    "Action": [
                        "kms:Describe*",
                        "kms:Get*",
                        "kms:List*",
                        "kms:RevokeGrant",
                    ],
                    "Effect": "Allow",
                    "Principal": {"AWS": f"arn:aws:iam::{account_id}:root"},
                    "Resource": "*",
                    "Sid": "Allow direct access to key metadata to the account",
                },
            ],
            "Version": "2012-10-17",
        }
    ),
    opts=pulumi.ResourceOptions(protect=True),
)
# This doesn't have a reason bar the instances were originally provisioned through the console
availability_zone = "eu-west-1b" if stack == "production" else "eu-west-1c"
identifier = (
    "navigator-production-rds-2023-10-17"
    if stack == "production"
    else "navigator-staging-rds-2023-03-27"
)

navigator_admin = aws.rds.Instance(
    "navigator-admin",
    allocated_storage=200,
    availability_zone=availability_zone,
    backup_retention_period=7,
    backup_window="22:22-22:52",
    ca_cert_identifier="rds-ca-rsa2048-g1",
    copy_tags_to_snapshot=True,
    db_subnet_group_name=db_subnet_group_name,
    deletion_protection=True,
    enabled_cloudwatch_logs_exports=[
        "postgresql",
        "upgrade",
    ],
    engine="postgres",
    engine_version="14.13",
    identifier=identifier,
    instance_class="db.x2g.large",
    iops=1000,
    kms_key_id=rds_kms_key.arn,
    license_model="postgresql-license",
    maintenance_window="sun:03:37-sun:04:07",
    max_allocated_storage=1000,
    monitoring_interval=60,
    monitoring_role_arn=rds_monitoring_role.arn,
    multi_az=True,
    network_type="IPV4",
    option_group_name="default:postgres-14",
    parameter_group_name="default.postgres14",
    performance_insights_enabled=True,
    performance_insights_kms_key_id=rds_kms_key.arn,
    performance_insights_retention_period=7,
    port=5432,
    skip_final_snapshot=True,
    storage_encrypted=True,
    storage_type=aws.rds.StorageType.IO1,
    tags={
        "map-migrated": "mig46666",
    },
    username=rds_username,
    db_name=rds_database,
    vpc_security_group_ids=vpc_security_group_ids,
    opts=pulumi.ResourceOptions(retain_on_delete=True, protect=True),
)

navigator_admin_read_replica = aws.rds.Instance(
    "navigator-admin-read-replica",
    allocated_storage=200,
    availability_zone=availability_zone,
    backup_window="22:22-22:52",
    ca_cert_identifier="rds-ca-rsa2048-g1",
    engine=navigator_admin.engine,
    engine_version=navigator_admin.engine_version,
    identifier=f"{identifier}-read-replica",
    instance_class="db.x2g.large",
    iops=1000,
    kms_key_id=rds_kms_key.arn,
    license_model="postgresql-license",
    maintenance_window="sun:03:37-sun:04:07",
    max_allocated_storage=1000,
    monitoring_interval=60,
    monitoring_role_arn=rds_monitoring_role.arn,
    network_type="IPV4",
    option_group_name="default:postgres-14",
    parameter_group_name="default.postgres14",
    performance_insights_enabled=True,
    performance_insights_kms_key_id=rds_kms_key.arn,
    performance_insights_retention_period=7,
    port=navigator_admin.port,
    replicate_source_db=navigator_admin.identifier,
    skip_final_snapshot=True,
    storage_encrypted=True,
    storage_type=aws.rds.StorageType.IO1,
    vpc_security_group_ids=vpc_security_group_ids,
    opts=pulumi.ResourceOptions(retain_on_delete=True, protect=True),
)
pulumi.export(
    "navigator_admin_read_replica_endpoint", navigator_admin_read_replica.endpoint
)
