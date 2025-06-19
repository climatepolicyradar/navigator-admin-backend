"""An AWS Python Pulumi program"""

import json
import sys
from pathlib import Path

import pulumi  # type: ignore
import pulumi_aws as aws  # type: ignore

sys.path.append(str(Path(__file__).parent.parent))

from util.naming import DEFAULT_TAGS

from resources.app_runner_service import (
    AppRunnerConfig,
    AppRunnerService,
    HealthCheckConfig,
    VpcConfig,
)
from resources.ecr_repository import ECRRepository, ECRRepositoryConfig, PolicyOptions
from resources.github_actions_role import GitHubActionsRole
from resources.util import validate_aws_account, validate_stack_and_branch

validate_aws_account()
validate_stack_and_branch()

RUNTIME = "python3.9"
CONFIG = pulumi.Config()

stack = pulumi.get_stack()
NAME_PREFIX = f"{stack}-{pulumi.get_project()}"


_S3_ACCESS_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": ["s3:*"],
            "Resource": [
                f"arn:aws:s3:::{CONFIG.require('bulk_import_bucket')}",
                f"arn:aws:s3:::{CONFIG.require('bulk_import_bucket')}/*",
                f"arn:aws:s3:::{CONFIG.require('database_dump_bucket')}",
                f"arn:aws:s3:::{CONFIG.require('database_dump_bucket')}/*",
            ],
            "Effect": "Allow",
        },
    ],
}

_ECR_ACCESS_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage",
                "ecr:DescribeImages",
                "ecr:GetAuthorizationToken",
                "ecr:BatchCheckLayerAvailability",
            ],
            "Resource": "*",
        }
    ],
}

_SSM_ACCESS_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": ["ssm:GetParameter", "ssm:GetParameters"],
            "Resource": [
                "arn:aws:ssm:eu-west-1:*:parameter/AdminBackend/AWS_ACCESS_KEY_ID",
                "arn:aws:ssm:eu-west-1:*:parameter/AdminBackend/AWS_SECRET_ACCESS_KEY",
            ],
        }
    ],
}


def _get_apprunner_instance_role() -> aws.iam.Role:
    apprunner_instance_role = aws.iam.Role(
        f"{NAME_PREFIX}-apprunner-instance-role-old",
        assume_role_policy=json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": "sts:AssumeRole",
                        "Effect": "Allow",
                        "Sid": "",
                        "Principal": {
                            "Service": "tasks.apprunner.amazonaws.com",
                        },
                    },
                ],
            }
        ),
        tags=DEFAULT_TAGS,
    )

    s3_access_policy = aws.iam.Policy(
        f"{NAME_PREFIX}-apprunner-s3-access-policy-old",
        policy=json.dumps(_S3_ACCESS_POLICY),
    )
    aws.iam.RolePolicyAttachment(
        f"{NAME_PREFIX}-apprunner-role-policy-attach-s3-access-policy-old",
        role=apprunner_instance_role.name,
        policy_arn=s3_access_policy.arn,
    )

    ssm_access_policy = aws.iam.Policy(
        f"{NAME_PREFIX}-apprunner-ssm-access-policy-old",
        policy=json.dumps(_SSM_ACCESS_POLICY),
    )
    aws.iam.RolePolicyAttachment(
        f"{NAME_PREFIX}-apprunner-role-policy-attach-ssm-access-policy-old",
        role=apprunner_instance_role.name,
        policy_arn=ssm_access_policy.arn,
    )

    return apprunner_instance_role


def _get_apprunner_access_role() -> aws.iam.Role:
    apprunner_access_role = aws.iam.Role(
        f"{NAME_PREFIX}-apprunner-access-role-old",
        assume_role_policy=json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": "sts:AssumeRole",
                        "Effect": "Allow",
                        "Sid": "",
                        "Principal": {
                            "Service": "build.apprunner.amazonaws.com",
                        },
                    },
                ],
            }
        ),
        tags=DEFAULT_TAGS,
    )

    ecr_access_policy = aws.iam.Policy(
        f"{NAME_PREFIX}-apprunner-ecr-access-policy-old",
        policy=json.dumps(_ECR_ACCESS_POLICY),
    )
    aws.iam.RolePolicyAttachment(
        f"{NAME_PREFIX}-apprunner-role-policy-attach-ecr-access-policy-old",
        role=apprunner_access_role.name,
        policy_arn=ecr_access_policy.arn,
    )

    return apprunner_access_role


def _create_backend_environment() -> dict[str, str]:
    # Create the environment config required for the backend service
    rds_username = CONFIG.require("rds_username")
    rds_password = CONFIG.require("rds_password")
    rds_address = CONFIG.require("rds_address")
    rds_database = CONFIG.require("rds_database")
    secret_key = CONFIG.require("secret_key")
    bulk_import_bucket = CONFIG.require("bulk_import_bucket")
    database_dump_bucket = CONFIG.require("database_dump_bucket")
    slack_webhook_url = CONFIG.require("slack_webhook_url")
    log_level = CONFIG.require("log_level")
    cache_bucket = CONFIG.require("cache_bucket")
    cdn_url = CONFIG.require("cdn_url")

    stack = pulumi.get_stack()
    backend_stack = pulumi.automation.select_stack(
        stack_name=f"climatepolicyradar/backend/{stack}",
        work_dir="../backend",
    )
    backend_token_secret_key = backend_stack.get_config(
        "backend_token_secret_key"
    ).value

    # Create SSM parameter references
    aws_access_key_parameter = aws.ssm.get_parameter(
        name="/AdminBackend/AWS_ACCESS_KEY_ID", with_decryption=True
    )
    aws_secret_key_parameter = aws.ssm.get_parameter(
        name="/AdminBackend/AWS_SECRET_ACCESS_KEY", with_decryption=True
    )

    environment: dict[str, str] = {
        "ADMIN_POSTGRES_USER": rds_username,
        "ADMIN_POSTGRES_PASSWORD": rds_password,
        "ADMIN_POSTGRES_HOST": rds_address,
        "ADMIN_POSTGRES_DATABASE": rds_database,
        "SECRET_KEY": secret_key,
        "BULK_IMPORT_BUCKET": bulk_import_bucket,
        "DATABASE_DUMP_BUCKET": database_dump_bucket,
        "CACHE_BUCKET": cache_bucket,
        "SLACK_WEBHOOK_URL": slack_webhook_url,
        "CDN_URL": cdn_url,
        "AWS_REGION": "eu-west-1",
        "TOKEN_SECRET_KEY": backend_token_secret_key,
        "LOG_LEVEL": log_level,
        "AWS_ACCESS_KEY_ID": aws_access_key_parameter.value,
        "AWS_SECRET_ACCESS_KEY": aws_secret_key_parameter.value,
    }

    return environment


def _create_apprunner_config() -> aws.apprunner.ServiceSourceConfigurationArgs:
    # Create the main config for the backend AppRunner service
    image_identifier = f"{CONFIG.require('ecr_uri')}:{CONFIG.require('docker_tag')}"
    env = _create_backend_environment()

    image_config = (
        aws.apprunner.ServiceSourceConfigurationImageRepositoryImageConfigurationArgs(
            port="8888",
            runtime_environment_variables=env,
        )
    )

    ecr_repo = aws.apprunner.ServiceSourceConfigurationImageRepositoryArgs(
        image_identifier=image_identifier,
        image_repository_type="ECR",
        image_configuration=image_config,
    )

    return aws.apprunner.ServiceSourceConfigurationArgs(
        auto_deployments_enabled=False,
        image_repository=ecr_repo,
        authentication_configuration=aws.apprunner.ServiceSourceConfigurationAuthenticationConfigurationArgs(
            access_role_arn=_get_apprunner_access_role().arn,
        ),
    )


def _create_backend_vpc_connector() -> aws.apprunner.VpcConnector:
    # Create a VPC connector to allow AppRunner instances to access private services
    vpc_connector_tags = dict(DEFAULT_TAGS)
    vpc_connector_tags["Name"] = f"{NAME_PREFIX}-vpc-connector"
    vpc_connector = aws.apprunner.VpcConnector(
        f"{NAME_PREFIX}-vpc-connector",
        vpc_connector_name=vpc_connector_tags["Name"],
        security_groups=[CONFIG.require("vpc_security_group_admin_backend")],
        subnets=[
            CONFIG.require("vpc_private_subnet_1_id"),
            CONFIG.require("vpc_private_subnet_2_id"),
            CONFIG.require("vpc_private_subnet_3_id"),
        ],
        tags=vpc_connector_tags,
    )

    return vpc_connector


def _create_backend_auto_scaling_config() -> (
    aws.apprunner.AutoScalingConfigurationVersion
):
    # Create a scaling configuration based on config
    scaling_config = aws.apprunner.AutoScalingConfigurationVersion(
        f"{NAME_PREFIX}-scaling-cfg",
        auto_scaling_configuration_name=f"{NAME_PREFIX}-scfg",
        max_concurrency=int(CONFIG.require("apprunner_backend_max_concurrency")),
        max_size=int(CONFIG.require("apprunner_backend_max_instance_count")),
        min_size=int(CONFIG.require("apprunner_backend_min_instance_count")),
        tags={
            "Name": f"{NAME_PREFIX}-scaling-cfg",
        },
    )

    return scaling_config


def create_admin_backend(
    vpc_connector: aws.apprunner.VpcConnector,
) -> aws.apprunner.Service:
    auto_scaling_config = _create_backend_auto_scaling_config()

    # Create the backend AppRunner app instance
    app_tags = dict(DEFAULT_TAGS)
    app_tags["Name"] = f"{NAME_PREFIX}-app"
    backend_app = aws.apprunner.Service(
        resource_name=f"{NAME_PREFIX}-app",
        service_name=f"{NAME_PREFIX}-app",
        instance_configuration=aws.apprunner.ServiceInstanceConfigurationArgs(
            cpu="2 vCPU",
            memory="4 GB",
            instance_role_arn=_get_apprunner_instance_role().arn,
        ),
        source_configuration=_create_apprunner_config(),
        network_configuration=aws.apprunner.ServiceNetworkConfigurationArgs(
            egress_configuration=aws.apprunner.ServiceNetworkConfigurationEgressConfigurationArgs(
                egress_type="VPC",
                vpc_connector_arn=vpc_connector.arn,
            ),
        ),
        auto_scaling_configuration_arn=auto_scaling_config.arn,
        health_check_configuration=aws.apprunner.ServiceHealthCheckConfigurationArgs(
            path="/health",
            protocol="HTTP",
            interval=10,
        ),
        tags=app_tags,
    )

    return backend_app


########################################################################
# Create ECR repo
########################################################################

# Create ECR repo in production account
ecr_repo = ECRRepository(
    "navigator-admin-backend",
    config=ECRRepositoryConfig(
        principal_service=PolicyOptions.APPRUNNER, image_scan_on_push=False
    ),
)

# Export the repository URL for use in CI/CD pipelines
pulumi.export("ecr_repository_url", ecr_repo.repository.repository_url)
pulumi.export("ecr_repository_name", ecr_repo.repository.name)

# Get the concrete repository URL value
repository_url = ecr_repo.repository.repository_url.apply(lambda url: url)
repository_url.apply(lambda url: pulumi.info(f"Repository URL: {url}"))
docker_tag = CONFIG.require("docker_tag")
pulumi.info(f"Docker tag: {docker_tag}")
image_identifier = ecr_repo.repository.repository_url.apply(
    lambda url: f"{url}:{docker_tag}"
)
image_identifier.apply(lambda id: pulumi.info(f"Final image identifier: {id}"))

########################################################################
# Create App Runner service
########################################################################

# Create old service
vpc_connector = _create_backend_vpc_connector()
backend_service = create_admin_backend(vpc_connector)
pulumi.export("apprunner_service_url", backend_service.service_url)

# Create new service
# Create config for the new service
config = AppRunnerConfig(
    max_concurrency=int(CONFIG.require("apprunner_backend_max_concurrency")),
    max_instances=int(CONFIG.require("apprunner_backend_max_instance_count")),
    min_instances=int(CONFIG.require("apprunner_backend_min_instance_count")),
    port=8888,
    cpu="2 vCPU",
    memory="4 GB",
    vpc_config=VpcConfig(
        vpc_connector_arn=vpc_connector.arn,
    ),
    health_check_config=HealthCheckConfig(
        path="/health",
        protocol="HTTP",
    ),
    s3_bucket_access={
        CONFIG.require("bulk_import_bucket"): ["*"],
        CONFIG.require("database_dump_bucket"): ["*"],
    },
    auto_deploy=True,
)

# Create the new service with the same configuration as the old one
new_backend = AppRunnerService(
    name=NAME_PREFIX,
    config=config,
    image_identifier=image_identifier,
    env_vars=_create_backend_environment(),
)


########################################################################
# Create GitHub Actions role
########################################################################

github_actions_role = GitHubActionsRole(
    name="navigator-admin-backend-github-actions",
)

########################################################################
# Create RDS instances
########################################################################


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
availability_zone = "eu-west-1c" if stack == "production" else "eu-west-1c"
availability_zone_read_replica = "eu-west-1b" if stack == "production" else "eu-west-1c"
identifier = (
    "navigator-production-rds-2023-10-17"
    if stack == "production"
    else "navigator-staging-rds-2023-03-27"
)

rds_instance_class = "db.x2g.4xlarge" if stack == "production" else "db.x2g.large"
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
    instance_class=rds_instance_class,
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
    availability_zone=availability_zone_read_replica,
    backup_window="22:22-22:52",
    ca_cert_identifier="rds-ca-rsa2048-g1",
    engine=navigator_admin.engine,
    engine_version=navigator_admin.engine_version,
    identifier=f"{identifier}-read-replica",
    instance_class=rds_instance_class,
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
