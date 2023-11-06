import json

import pulumi
import pulumi_aws as aws
from util.naming import DEFAULT_TAGS, NAME_PREFIX

CONFIG = pulumi.config.Config()
# TODO: we'll probably eventually needs some S3 access
# _S3_ACCESS_POLICY = {
#     "Version": "2012-10-17",
#     "Statement": [
#         {
#             "Action": ["s3:PutObject"],
#             "Resource": f"arn:aws:s3:::{CONFIG.require('pipeline_s3_bucket')}/*",
#             "Effect": "Allow",
#         },
#     ],
# }

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


def _get_apprunner_instance_role() -> aws.iam.Role:
    apprunner_instance_role = aws.iam.Role(
        f"{NAME_PREFIX}-apprunner-instance-role",
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

    # TODO: Add some s3 access when needed
    # s3_access_policy = aws.iam.Policy(
    #     f"{NAME_PREFIX}-apprunner-s3-access-policy",
    #     policy=json.dumps(_S3_ACCESS_POLICY),
    # )
    # aws.iam.RolePolicyAttachment(
    #     f"{NAME_PREFIX}-apprunner-role-policy-attach-s3-access-policy",
    #     role=apprunner_instance_role.name,
    #     policy_arn=s3_access_policy.arn,
    # )

    return apprunner_instance_role


def _get_apprunner_access_role() -> aws.iam.Role:
    apprunner_access_role = aws.iam.Role(
        f"{NAME_PREFIX}-apprunner-access-role",
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
        f"{NAME_PREFIX}-apprunner-ecr-access-policy",
        policy=json.dumps(_ECR_ACCESS_POLICY),
    )
    aws.iam.RolePolicyAttachment(
        f"{NAME_PREFIX}-apprunner-role-policy-attach-ecr-access-policy",
        role=apprunner_access_role.name,
        policy_arn=ecr_access_policy.arn,
    )

    return apprunner_access_role


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


def _create_backend_environment() -> dict[str, str]:
    # Create the environment config required for the backend service
    rds_username = CONFIG.require("rds_username")
    rds_password = CONFIG.require("rds_password")
    rds_address = CONFIG.require("rds_address")
    rds_database = CONFIG.require("rds_database")
    secret_key = CONFIG.require("secret_key")

    environment: dict[str, str] = {
        "ADMIN_POSTGRES_USER": rds_username,
        "ADMIN_POSTGRES_PASSWORD": rds_password,
        "ADMIN_POSTGRES_HOST": rds_address,
        "ADMIN_POSTGRES_DATABASE": rds_database,
        "SECRET_KEY": secret_key,
    }

    return environment


def _create_apprunner_config() -> aws.apprunner.ServiceSourceConfigurationArgs:
    # Create the main config for the backend AppRunner service
    account_id = aws.get_caller_identity().account_id
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


def create_admin_backend() -> aws.apprunner.Service:
    auto_scaling_config = _create_backend_auto_scaling_config()
    vpc_connector = _create_backend_vpc_connector()

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
