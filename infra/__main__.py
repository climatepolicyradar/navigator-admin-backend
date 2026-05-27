"""
                    .--.
                   (o  o)
                   /    \
                  /|    |\
                  ^^    ^^

    🚧 migration in progress 🚧

    App Runner → ECS Express
    STATUS
  → ECS Express is live behind CloudFront
  → Cleanup and refactor work to be completed, with the infra code moved to the infra
    directory in the service

    Roadmap
  → Remove old App Runner service and related resources

    This file is temporary and mid-refactor.
"""

import json
import sys
from pathlib import Path

import pulumi  # type: ignore
import pulumi_aws as aws  # type: ignore

sys.path.append(str(Path(__file__).parent.parent))

from pulumi_aws import ecs, get_caller_identity, iam
from pulumi_aws.ecs.express_gateway_service import (
    ExpressGatewayService,
    ExpressGatewayServiceNetworkConfigurationArgs,
    ExpressGatewayServicePrimaryContainerArgs,
    ExpressGatewayServicePrimaryContainerEnvironmentArgs,
    ExpressGatewayServiceScalingTargetArgs,
)

from infra.resources.app_runner_service import (
    AppRunnerConfig,
    AppRunnerService,
    HealthCheckConfig,
    VpcConfig,
)
from infra.resources.ecr_repository import ECRRepository, ECRRepositoryConfig
from infra.resources.github_actions_role import GitHubActionsRole
from infra.resources.naming import DEFAULT_TAGS
from infra.resources.util import validate_aws_account, validate_stack_and_branch

validate_aws_account()
validate_stack_and_branch()

CONFIG = pulumi.Config()

stack = pulumi.get_stack()
name = "admin-backend"
NAME_PREFIX = f"{stack}-{pulumi.get_project()}"


def _create_backend_environment() -> dict[str, str]:
    # Create the environment config required for the backend service
    rds_username = CONFIG.require("rds_username")
    rds_password = CONFIG.require("rds_password")
    rds_address = CONFIG.require("rds_address")
    rds_database = CONFIG.require("rds_database")
    secret_key = CONFIG.require("secret_key")
    bulk_import_bucket = CONFIG.require("bulk_import_bucket")
    database_dump_bucket = CONFIG.require("database_dump_bucket")
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

    environment: dict[str, str] = {
        "ADMIN_POSTGRES_USER": rds_username,
        "ADMIN_POSTGRES_PASSWORD": rds_password,
        "ADMIN_POSTGRES_HOST": rds_address,
        "ADMIN_POSTGRES_DATABASE": rds_database,
        "SECRET_KEY": secret_key,
        "BULK_IMPORT_BUCKET": bulk_import_bucket,
        "DATABASE_DUMP_BUCKET": database_dump_bucket,
        "CACHE_BUCKET": cache_bucket,
        "CDN_URL": cdn_url,
        "AWS_REGION": "eu-west-1",
        "TOKEN_SECRET_KEY": backend_token_secret_key,
        "LOG_LEVEL": log_level,
        "ENV": pulumi.get_stack(),
    }
    if stack == "production":
        environment["SLACK_OAUTH_TOKEN"] = CONFIG.require("slack_oauth_token")
        environment["SLACK_CHANNEL"] = CONFIG.require("slack_channel")
        environment["SLACK_GROUP_ID_APPLICATION_ENGINEERS"] = CONFIG.require(
            "application_engineers_slack_group_id"
        )

    return environment


def _create_backend_vpc_connector() -> aws.apprunner.VpcConnector:
    # Create a VPC connector to allow AppRunner instances to access private services
    vpc_connector_tags = {
        "CPR-Created-By": "pulumi",
        "CPR-Pulumi-Stack-Name": pulumi.get_stack(),
        "CPR-Pulumi-Project-Name": pulumi.get_project(),
        "CPR-Tag": NAME_PREFIX,
    }
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


########################################################################
# Create ECR repo
########################################################################

ecr_repo = ECRRepository(
    "navigator-admin-backend",
    config=ECRRepositoryConfig(image_scan_on_push=False),
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
pulumi.export("apprunner_service_url", new_backend.service.service_url)
pulumi.export("new_apprunner_service_url", new_backend.service.service_url)


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

# GOTCHA: STAGING_DB_NAME
# annoyingly the db_name wasn't set when provisioning staging
# and can't be changed post-launch without replacing it,
# we have to set it to nothing
rds_database = None if stack == "staging" else CONFIG.require("rds_database")
rds_username = CONFIG.require("rds_username")
rds_password = CONFIG.require("rds_password")
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
availability_zone = "eu-west-1c" if stack == "production" else "eu-west-1b"
availability_zone_read_replica = "eu-west-1b" if stack == "production" else "eu-west-1c"
identifier = (
    "navigator-production-rds-2023-10-17"
    if stack == "production"
    else "navigator-staging-rds-2023-03-27"
)

rds_instance_class = "db.t4g.large" if stack == "production" else "db.t4g.small"
navigator_admin = aws.rds.Instance(
    "navigator-admin",
    apply_immediately=True,
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
    engine_version="14.17",
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
    tags={},
    username=rds_username,
    db_name=rds_database,
    password=CONFIG.require("rds_password"),
    vpc_security_group_ids=vpc_security_group_ids,
    opts=pulumi.ResourceOptions(retain_on_delete=True, protect=True),
)

navigator_admin_read_replica = aws.rds.Instance(
    "navigator-admin-read-replica",
    apply_immediately=True,
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
aws.ssm.Parameter(
    "/navigator-admin-backend/rds/NAVIGATOR_ADMIN_DATABASE_PASSWORD",
    name="/navigator-admin-backend/rds/NAVIGATOR_ADMIN_DATABASE_PASSWORD",
    type=aws.ssm.ParameterType.SECURE_STRING,
    value=navigator_admin.password,
)
aws.ssm.Parameter(
    "/navigator-admin-backend/rds/NAVIGATOR_ADMIN_DATABASE_USERNAME",
    name="/navigator-admin-backend/rds/NAVIGATOR_ADMIN_DATABASE_USERNAME",
    type=aws.ssm.ParameterType.SECURE_STRING,
    value=navigator_admin.username,
)
aws.ssm.Parameter(
    "/navigator-admin-backend/rds/NAVIGATOR_ADMIN_DATABASE_ENDPOINT",
    name="/navigator-admin-backend/rds/NAVIGATOR_ADMIN_DATABASE_ENDPOINT",
    type=aws.ssm.ParameterType.SECURE_STRING,
    value=navigator_admin.endpoint,
)

aws.ssm.Parameter(
    "/navigator-admin-backend/rds/NAVIGATOR_ADMIN_DATABASE_DB_NAME",
    name="/navigator-admin-backend/rds/NAVIGATOR_ADMIN_DATABASE_DB_NAME",
    type=aws.ssm.ParameterType.SECURE_STRING,
    # GOTCHA: STAGING_DB_NAME
    # annoyingly the db_name wasn't set when provisioning staging
    # so we just read the config value
    value=CONFIG.require("rds_database"),
)

pulumi.export(
    "navigator_admin_read_replica_endpoint", navigator_admin_read_replica.endpoint
)

########################################################################
# Create S3 Buckets
########################################################################
rds_backups = aws.s3.Bucket(
    f"{stack}-rds-backups",
    bucket=f"cpr-{stack}-rds",
    versioning=aws.s3.BucketVersioningArgs(enabled=True),
    lifecycle_rules=[
        aws.s3.BucketLifecycleRuleArgs(
            enabled=True,
            id="noncurrent-version-cleanup-90d",
            noncurrent_version_expiration=aws.s3.BucketLifecycleRuleNoncurrentVersionExpirationArgs(
                days=90,
            ),
        ),
        aws.s3.BucketLifecycleRuleArgs(
            enabled=True,
            id="SQL-Dump-Retention-3weeks",
            prefix="dumps/",
            expiration=aws.s3.BucketLifecycleRuleExpirationArgs(
                days=21,
            ),
        ),
    ],
    request_payer="BucketOwner",
    server_side_encryption_configuration=aws.s3.BucketServerSideEncryptionConfigurationArgs(
        rule=aws.s3.BucketServerSideEncryptionConfigurationRuleArgs(
            apply_server_side_encryption_by_default=aws.s3.BucketServerSideEncryptionConfigurationRuleApplyServerSideEncryptionByDefaultArgs(
                sse_algorithm="AES256",
            ),
            bucket_key_enabled=True,
        ),
    ),
    tags=dict(DEFAULT_TAGS),
    opts=pulumi.ResourceOptions(protect=True),
)

bulk_import_bucket = aws.s3.get_bucket(bucket=f"cpr-{stack}-bulkimport")
cpr_document_cache_bucket = aws.s3.get_bucket(bucket=f"cpr-{stack}-document-cache")

s3_bucket_arns = [
    rds_backups.arn,
    cpr_document_cache_bucket.arn,
    bulk_import_bucket.arn,
]

if stack == "production":
    production_document_pdf_upload_store = aws.s3.Bucket(
        "production-document-pdf-upload-store",
        bucket="cpr-prod-cclw-document-admin-store",
        versioning=aws.s3.BucketVersioningArgs(enabled=True),
        cors_rules=[
            aws.s3.BucketCorsRuleArgs(
                allowed_headers=["*"],
                allowed_methods=[
                    "PUT",
                    "POST",
                    "DELETE",
                ],
                allowed_origins=["https://*.retool.com"],
            ),
            aws.s3.BucketCorsRuleArgs(
                allowed_methods=["GET"],
                allowed_origins=["*"],
            ),
        ],
        request_payer="BucketOwner",
        server_side_encryption_configuration=aws.s3.BucketServerSideEncryptionConfigurationArgs(
            rule=aws.s3.BucketServerSideEncryptionConfigurationRuleArgs(
                apply_server_side_encryption_by_default=aws.s3.BucketServerSideEncryptionConfigurationRuleApplyServerSideEncryptionByDefaultArgs(
                    sse_algorithm="AES256",
                ),
                bucket_key_enabled=True,
            ),
        ),
        lifecycle_rules=[
            aws.s3.BucketLifecycleRuleArgs(
                enabled=True,
                id="noncurrent-version-cleanup-90d",
                noncurrent_version_expiration=aws.s3.BucketLifecycleRuleNoncurrentVersionExpirationArgs(
                    days=90,
                ),
            ),
        ],
        tags=dict(DEFAULT_TAGS),
        opts=pulumi.ResourceOptions(protect=True),
    )

    s3_bucket_arns.extend([production_document_pdf_upload_store.arn, rds_backups.arn])


# pulumi config
caller_identity = get_caller_identity()

tags = {
    "CPR-Created-By": "pulumi",
    "CPR-Pulumi-Stack-Name": stack,
    "CPR-Pulumi-Project-Name": pulumi.get_project(),
    "CPR-Tag": NAME_PREFIX,
    "Environment": stack,
}


# -----
# ECS Express Mode
# -----

ecs_write_s3_policy = iam.Policy(
    f"{name}-write-s3-policy",
    name=f"{name}-write-s3-policy",
    description="Policy to allow reading and writing data files from/to S3",
    policy=pulumi.Output.json_dumps(
        (
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "s3:GetObject",
                            "s3:ListBucket",
                            "s3:PutObject",
                            "s3:DeleteObject",
                        ],
                        "Resource": [
                            *s3_bucket_arns,
                            *[
                                pulumi.Output.from_input(arn).apply(lambda a: f"{a}/*")
                                for arn in s3_bucket_arns
                            ],
                        ],
                    }
                ],
            }
        )
    ),
)

# Task role: runtime permissions (S3 read) — reuses the same policy as AppRunner
ecs_task_role = iam.Role(
    f"{name}-ecs-task-role",
    name=f"{name}-ecs-task-role",
    assume_role_policy=iam.get_policy_document(
        statements=[
            iam.GetPolicyDocumentStatementArgs(
                effect="Allow",
                principals=[
                    iam.GetPolicyDocumentStatementPrincipalArgs(
                        type="Service",
                        identifiers=["ecs-tasks.amazonaws.com"],
                    )
                ],
                actions=["sts:AssumeRole"],
            )
        ]
    ).json,
)
iam.RolePolicyAttachment(
    f"{name}-ecs-task-reads3-policy-attachment",
    role=ecs_task_role.name,
    policy_arn=ecs_write_s3_policy.arn,
)


# Execution role: pulls the image and injects secrets at container startup
ecs_task_execution_role = iam.Role(
    f"{name}-{stack}-ecs-task-execution-role",
    name=f"{name}-{stack}-ecs-task-execution-role",
    assume_role_policy=iam.get_policy_document(
        statements=[
            iam.GetPolicyDocumentStatementArgs(
                effect="Allow",
                principals=[
                    iam.GetPolicyDocumentStatementPrincipalArgs(
                        type="Service",
                        identifiers=["ecs-tasks.amazonaws.com"],
                    )
                ],
                actions=["sts:AssumeRole"],
            ),
            iam.GetPolicyDocumentStatementArgs(
                effect="Allow",
                principals=[
                    iam.GetPolicyDocumentStatementPrincipalArgs(
                        type="AWS",
                        identifiers=[
                            f"arn:aws:iam::{account_id}:role/{github_actions_role.name}"
                        ],
                    )
                ],
                actions=["sts:AssumeRole"],
            ),
        ]
    ).json,
    managed_policy_arns=[
        "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
    ],
)


# Infrastructure role: manages the ALB, target groups, and security groups
ecs_infrastructure_role = iam.Role(
    f"{name}-{stack}-ecs-infrastructure-role",
    name=f"{name}-{stack}-ecs-infrastructure-role",
    assume_role_policy=iam.get_policy_document(
        statements=[
            iam.GetPolicyDocumentStatementArgs(
                effect="Allow",
                principals=[
                    iam.GetPolicyDocumentStatementPrincipalArgs(
                        type="Service",
                        identifiers=["ecs.amazonaws.com"],
                    )
                ],
                actions=["sts:AssumeRole"],
            ),
            iam.GetPolicyDocumentStatementArgs(
                effect="Allow",
                principals=[
                    iam.GetPolicyDocumentStatementPrincipalArgs(
                        type="AWS",
                        identifiers=[
                            f"arn:aws:iam::{account_id}:role/{github_actions_role.name}"
                        ],
                    )
                ],
                actions=["sts:AssumeRole"],
            ),
        ]
    ).json,
    managed_policy_arns=[
        "arn:aws:iam::aws:policy/service-role/AmazonECSInfrastructureRoleforExpressGatewayServices",
    ],
)

ecs_cluster = ecs.Cluster(
    f"{name}-{stack}-ecs-cluster",
    name=f"{name}-{stack}",
    settings=[
        ecs.ClusterSettingArgs(
            name="containerInsights",
            value="enabled",
        )
    ],
)

env_vars = _create_backend_environment()

# -----
# ECS networking — public-facing ALB, locked to CloudFront
# -----

ecs_alb_security_group = aws.ec2.SecurityGroup(
    f"{name}-{stack}-ecs-alb-sg",
    name=f"{name}-{stack}-ecs-alb-sg",
    description="Allows inbound HTTP from CloudFront to the Express Gateway ALB",
    vpc_id=CONFIG.require("vpc_id"),
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            description="HTTP from CloudFront edge locations",
            from_port=80,
            to_port=80,
            protocol="tcp",
            prefix_list_ids=[CONFIG.require("cloudfront_origin_prefix_list_id")],
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            from_port=0,
            to_port=0,
            protocol="-1",
            cidr_blocks=["0.0.0.0/0"],
        ),
    ],
    tags=dict(DEFAULT_TAGS),
)

aws.ec2.SecurityGroupRule(
    f"{name}-{stack}-rds-ingress-from-ecs",
    type="ingress",
    from_port=5432,
    to_port=5432,
    protocol="tcp",
    security_group_id=CONFIG.require("rds_vpc_security_group_id"),
    source_security_group_id=ecs_alb_security_group.id,
    description="Allow ECS Express tasks to reach Postgres",
)

primary_container = ExpressGatewayServicePrimaryContainerArgs(
    image=ecr_repo.repository.repository_url.apply(lambda url: f"{url}:latest"),
    container_port=8888,
    environments=[
        ExpressGatewayServicePrimaryContainerEnvironmentArgs(name=k, value=v)
        for k, v in env_vars.items()
    ],
)

ecs_express_service = ExpressGatewayService(
    f"{name}-{stack}-ecs-express-service",
    service_name=f"{name}-{stack}",
    cluster=ecs_cluster.arn,
    execution_role_arn=ecs_task_execution_role.arn,
    infrastructure_role_arn=ecs_infrastructure_role.arn,
    task_role_arn=ecs_task_role.arn,
    primary_container=primary_container,
    health_check_path="/health",
    cpu="1024",
    memory="2048",
    scaling_targets=[
        ExpressGatewayServiceScalingTargetArgs(
            auto_scaling_metric="AVERAGE_CPU",
            auto_scaling_target_value=70,
            min_task_count=1,
            max_task_count=4,
        ),
    ],
    network_configurations=[
        ExpressGatewayServiceNetworkConfigurationArgs(
            security_groups=[ecs_alb_security_group.id],
            subnets=[
                CONFIG.require("vpc_public_subnet_1_id"),
                CONFIG.require("vpc_public_subnet_2_id"),
                CONFIG.require("vpc_public_subnet_3_id"),
            ],
        )
    ],
)
pulumi.export(
    "ecs_express_service_url",
    ecs_express_service.ingress_paths.apply(
        lambda paths: paths[0].endpoint if paths else None
    ),
)
