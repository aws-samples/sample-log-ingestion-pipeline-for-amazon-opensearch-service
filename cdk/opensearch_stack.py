from aws_cdk import Stack    
from aws_cdk import aws_opensearchservice as opensearchservice
from constructs import Construct
from aws_cdk.aws_iam import ServicePrincipal, Role, ManagedPolicy, PolicyDocument, PolicyStatement, Effect
from  aws_cdk.aws_sqs import Queue
class OpensearchStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, cloudwatch_stack, ingestion_stack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        environment_params = self.node.try_get_context("environment")
        domain_name = environment_params["domain_name"]
        user_name = environment_params["user_name"]
        user_password = environment_params["user_password"]

        self.blog_opensearch_domain = self._create_opensearch_domain(domain_name, 
                            user_name, user_password, cloudwatch_stack, ingestion_stack)
    


    def _create_opensearch_domain(self, domain_name: str, user_name: str, 
                user_password:str, cloudwatch_stack: Stack, 
                ingestion_stack: Stack) -> opensearchservice.CfnDomain:


        opensearch_domain = opensearchservice.CfnDomain(self, domain_name,
        access_policies = {
                'Version': '2012-10-17',
                'Statement': [
                    {
                        'Effect': 'Allow',
                        'Principal': {'AWS': '*'},
                        'Action': [
                            'es:EsHttp*'
                        ],
                        'Resource': f'arn:{self.partition}:es:{self.region}:{self.account}:domain/{domain_name}/*',
                    },
                    {
                        'Effect': 'Allow',
                        'Principal': {'AWS': f'{ingestion_stack.pipeline_role.role_arn}'},
                        'Action': [
                            'es:*'
                        ],
                        'Resource': f'arn:{self.partition}:es:{self.region}:{self.account}:domain/{domain_name}/*'

                    }
                ]
            },
        # advanced_options = {
        # "advanced_options_key": "advancedOptions"
        # },
        advanced_security_options = opensearchservice.CfnDomain.
            AdvancedSecurityOptionsInputProperty(enabled=True,
            internal_user_database_enabled = True,
            master_user_options = opensearchservice.CfnDomain.MasterUserOptionsProperty(
            master_user_name = user_name,
            master_user_password = user_password
            # master_user_arn = pipeline_role.role_arn
            ),
        ),
        cluster_config = opensearchservice.CfnDomain.ClusterConfigProperty(
        dedicated_master_count = 3,
        dedicated_master_enabled = True,
        dedicated_master_type = "m6g.large.search",
        instance_count = 3,
        instance_type = "r6g.xlarge.search",
        warm_enabled = False,
        zone_awareness_config = opensearchservice.CfnDomain.ZoneAwarenessConfigProperty(
            availability_zone_count=3
        ),
        zone_awareness_enabled = True
        ),
        domain_name = domain_name,

        domain_endpoint_options=opensearchservice.CfnDomain.DomainEndpointOptionsProperty(
        enforce_https = True
        ),

        ebs_options = opensearchservice.CfnDomain.EBSOptionsProperty(
            ebs_enabled = True,
            volume_size = 20,
            volume_type = "gp3"
        ), 
        encryption_at_rest_options = opensearchservice.CfnDomain.EncryptionAtRestOptionsProperty(
            enabled = True
        ),
        engine_version = "OpenSearch_2.19",
        log_publishing_options = {
            "SEARCH_SLOW_LOGS": opensearchservice.CfnDomain.LogPublishingOptionProperty(
                cloud_watch_logs_log_group_arn = cloudwatch_stack.search_slow_log_group.log_group_arn,
                enabled = True
            ),
            "ES_APPLICATION_LOGS": opensearchservice.CfnDomain.LogPublishingOptionProperty(
                cloud_watch_logs_log_group_arn = cloudwatch_stack.error_log_group.log_group_arn,
                enabled = True
            ),
            "INDEX_SLOW_LOGS": opensearchservice.CfnDomain.LogPublishingOptionProperty(
                cloud_watch_logs_log_group_arn = cloudwatch_stack.index_slow_log_group.log_group_arn,
                enabled = True
            ),
            "AUDIT_LOGS": opensearchservice.CfnDomain.LogPublishingOptionProperty(
                cloud_watch_logs_log_group_arn = cloudwatch_stack.audit_log_group.log_group_arn,
                enabled = True
            )
        },
        node_to_node_encryption_options = opensearchservice.CfnDomain.NodeToNodeEncryptionOptionsProperty(
            enabled = True
        ),
        snapshot_options = opensearchservice.CfnDomain.SnapshotOptionsProperty(
            automated_snapshot_start_hour = 0
        ),
        software_update_options = opensearchservice.CfnDomain.SoftwareUpdateOptionsProperty(
            auto_software_update_enabled = True
        )
        )

        return opensearch_domain
