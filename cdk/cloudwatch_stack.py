from aws_cdk import Stack
from aws_cdk import aws_logs as logs
from constructs import Construct
from aws_cdk import RemovalPolicy
from aws_cdk import aws_iam as iam

class CloudWatchStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Retriving the cloudwatch log group names from cdk.json
        environment_params = self.node.try_get_context("environment")

        domain_name = environment_params["domain_name"]

        audit_log_group_name = f"/aws/OpenSearchService/domains/{domain_name}/audit-logs"
        search_slow_log_group_name = f"/aws/OpenSearchService/domains/{domain_name}/search-logs"
        index_slow_log_group_name =  f"/aws/OpenSearchService/domains/{domain_name}/index-logs"
        error_log_group_name = f"/aws/OpenSearchService/domains/{domain_name}/application-logs"
        osis_log_group_name = f"/aws/vendedlogs/OpenSearchIngestion/apache-log-pipeline/audit-logs"

        self.audit_log_group = self._create_log_group(audit_log_group_name, 'audit_log_group')
        self.search_slow_log_group = self._create_log_group(search_slow_log_group_name, 'search_slow_log_group')
        self.index_slow_log_group = self._create_log_group(index_slow_log_group_name, 'index_slow_log_group')
        self.error_log_group = self._create_log_group(error_log_group_name, 'error_log_group')
        self.osis_log_group = self._create_log_group(osis_log_group_name, 'osis_log_group')

    def _create_log_group(self, log_group_name: str, logical_name: str) -> logs.LogGroup:

        print(f"Creating the Cloudwatch Log Group : {log_group_name}")

        cloudwatch_log_group: logs.LogGroup = logs.LogGroup(
            self,
            logical_name,
            log_group_name = log_group_name,
            retention = logs.RetentionDays.THREE_MONTHS,
            removal_policy = RemovalPolicy.DESTROY    
        )

        # adding permissions for the Opensaerch Service
        cloudwatch_log_group.add_to_resource_policy(
            iam.PolicyStatement(
            actions=["logs:CreateLogStream", "logs:PutLogEvents"],
            principals=[iam.ServicePrincipal("es.amazonaws.com")],
            resources=[cloudwatch_log_group.log_group_arn]
            )
        )
        return cloudwatch_log_group
        