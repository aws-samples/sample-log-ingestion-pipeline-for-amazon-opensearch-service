from aws_cdk import Stack
from constructs import Construct
from aws_cdk.aws_osis import CfnPipeline


class PipelineStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, opensearch_stack, 
                cloudwatch_stack, ingestion_stack, **kwargs) -> None:
        
        super().__init__(scope, construct_id, **kwargs)

        environment_params = self.node.try_get_context("environment")

        domain_name = environment_params["domain_name"]

        apache_log_pipeline = self._create_opensearch_ingest_pipeline(cloudwatch_stack, 
                    opensearch_stack, ingestion_stack, domain_name)
    
    def _create_opensearch_ingest_pipeline(self, cloudwatch_stack: Stack, 
                    opensearch_stack: Stack, ingestion_stack:Stack, domain_name) -> CfnPipeline:

        apache_log_pipeline = CfnPipeline(
                self, 
                "apache-log-pipeline",
                min_units = 2,
                max_units = 3,
                pipeline_name=f"apache-log-pipeline",
                log_publishing_options = CfnPipeline.LogPublishingOptionsProperty(
                    cloud_watch_log_destination = CfnPipeline.CloudWatchLogDestinationProperty(
                        log_group = cloudwatch_stack.osis_log_group.log_group_name),
                    is_logging_enabled = True),
                pipeline_configuration_body = f"""
                    version: "2"
                    apache-log-pipeline:
                        source:
                            s3:
                                acknowledgments: true
                                notification_type: "sqs"
                                compression: gzip
                                codec:
                                    newline:
                                sqs:
                                    queue_url: "{ingestion_stack.updated_s3_event_sqs_queue.queue_url}"
                                    visibility_timeout: "120s"
                                aws:
                                    region: "{self.region}"
                                    sts_role_arn: "arn:aws:iam::{self.account}:role/{ingestion_stack.updated_pipeline_role.role_name}"
                        processor:
                            - grok:
                                match:
                                    message: [ "%{{COMBINEDAPACHELOG}}" ]
                            - date:
                                destination: "@ingestion_timestamp"
                                from_time_received: true
                            - add_entries:
                                entries:
                                  - key: "@log_type"
                                    value: "apache-access-log"
                                    overwrite_if_key_exists: false

                        sink:
                            - opensearch:
                                hosts:
                                    [
                                    "https://{opensearch_stack.blog_opensearch_domain.attr_domain_endpoint}",
                                    ]
                                aws:
                                    sts_role_arn: "arn:aws:iam::{self.account}:role/{ingestion_stack.updated_pipeline_role.role_name}"
                                    region: "{self.region}"
                                index: "apache-access-log-%{{yyyy-MM}}"
                            """
                )
        return apache_log_pipeline
    