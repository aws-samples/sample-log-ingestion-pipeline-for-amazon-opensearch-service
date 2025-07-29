from aws_cdk.aws_iam import ArnPrincipal, Role, ServicePrincipal, ManagedPolicy, PolicyDocument, PolicyStatement, Effect
from aws_cdk.aws_s3 import Bucket, BucketAccessControl, BucketEncryption, EventType, NotificationKeyFilter
from constructs import Construct
from aws_cdk import Stack, RemovalPolicy
from aws_cdk.aws_s3_deployment import BucketDeployment, Source
from  aws_cdk.aws_sqs import Queue
from aws_cdk.aws_osis import CfnPipeline
from aws_cdk.aws_s3_notifications import SqsDestination

class IngestionStack(Stack):
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        environment_params = self.node.try_get_context("environment")

        domain_name = environment_params["domain_name"]

        bucket_name = f"opensearch-logging-blog-{self.account}-{domain_name}"
        data_bucket = self._create_s3_bucket(bucket_name)

        # log_data_deployment = self._upload_data_to_buckets(data_bucket)
        # log_data_deployment.node.add_dependency(data_bucket)

        pipeline_role_name = f"apache-log-ingestion-{domain_name}"
        self.pipeline_role = self._create_pipeline_service_role(pipeline_role_name)

        sqs_queue_name = f"log-event-queue-{domain_name}"
        self.s3_event_sqs_queue = self._create_sqs_queue(sqs_queue_name, data_bucket, 
                                                self.pipeline_role)
    
    
        self.updated_pipeline_role, self.updated_s3_event_sqs_queue = self._add_iam_permissions(
            self.s3_event_sqs_queue, self.pipeline_role, data_bucket)
        
        self._add_event_notifications(data_bucket, self.updated_s3_event_sqs_queue)




    def _create_s3_bucket(self, bucket_name : str) -> Bucket :

        data_bucket:Bucket = Bucket(
            self,
            "DataBucket",
            bucket_name = bucket_name,
            public_read_access = False,
            access_control = BucketAccessControl.BUCKET_OWNER_FULL_CONTROL,
            encryption = BucketEncryption.S3_MANAGED,
            removal_policy = RemovalPolicy.DESTROY
        )
        return data_bucket
    
    def _upload_data_to_buckets(self, data_bucket: Bucket) -> BucketDeployment:
        
        log_file_deployment: BucketDeployment = BucketDeployment(
            self,
            "log-file-deployment",
            sources=[Source.asset("./apache_log_data")],
            destination_bucket = data_bucket,
            destination_key_prefix = "apache-log-data",
        )
        return log_file_deployment
    
    def _create_pipeline_service_role(self, pipeline_role_name : str) -> Role:
        
        # creating a service role for the openserach pipeline
        pipeline_role: Role = Role(
            self,
            "osi-pipeline-role",
            role_name = pipeline_role_name,
            assumed_by = ServicePrincipal("osis-pipelines.amazonaws.com")
        )

        ManagedPolicy(
            self,
            "opensearch-describe-policy",
            roles=[pipeline_role],
            document=PolicyDocument(
                statements=[
                    PolicyStatement(
                        effect=Effect.ALLOW,
                        actions=[
                            "es:DescribeDomainNodes",
                            "es:DescribeDomainHealth",
                            "es:ESHttpHead",
                            "es:ESHttpGet",
                            "es:DescribeDomain",
                            "es:DescribeDomainConfig"
                        ],
                        resources=[
                                f"arn:aws:es:*:{self.account}:domain/*"
                        ],
                    )
                ])
        )

        return pipeline_role


    def _create_sqs_queue(self, queue_name:str, data_bucket:Bucket, pipeline_role:Role) -> Queue:

        log_event_queue : Queue = Queue(
            self,
            "log-event-queue",
            queue_name = queue_name
        )

        log_event_queue.grant_consume_messages(pipeline_role)
        return log_event_queue
    
    def _add_event_notifications(self, data_bucket:Bucket, s3_event_sqs_queue: Queue) -> None:
        
        s3_notification = SqsDestination(s3_event_sqs_queue)
        data_bucket.add_event_notification(EventType.OBJECT_CREATED,
                                    s3_notification)
                                    #,NotificationKeyFilter(prefix = "apache-log-data/"))
        

    def _add_iam_permissions(self, log_event_queue : Queue, pipeline_role : Role, 
                    data_bucket:Bucket) -> object :
        
        log_event_queue.add_to_resource_policy(
            PolicyStatement(
                actions=["sqs:*"],
                resources=[log_event_queue.queue_arn],
                principals=[ServicePrincipal("s3.amazonaws.com")],
                conditions={
                    "ArnEquals": {
                        "aws:SourceArn": f"arn:aws:s3:::{data_bucket.bucket_name}"
                    }
                }
            )
        )

        ManagedPolicy(
            self,
            "other-resource-policies",
            roles=[pipeline_role],
            document=PolicyDocument(
                statements=[
                    PolicyStatement(
                        effect=Effect.ALLOW,
                        actions=[
                            "es:ESHttp*"
                        ],
                        resources=[
                            f"arn:{self.partition}:es:{self.region}:{self.account}:domain/*"
                        ],
                    ),
                    PolicyStatement(
                        effect=Effect.ALLOW,
                        actions=["sqs:DeleteMessage",
                                "sqs:ReceiveMessage",
                                "sqs:GetQueueAttributes",
                                "sqs:GetQueueUrl",
                                "sqs:ChangeMessageVisibility"],
                        resources=[f"{log_event_queue.queue_arn}"],
                    ),
                    PolicyStatement(
                        effect=Effect.ALLOW,
                        actions=["s3:GetObject",
                            "s3:ListBucket"
                        ],
                        resources=[
                            data_bucket.bucket_arn,
                            f"{data_bucket.bucket_arn}/*",
                        ]
                    )

                ]
            )
        )
        return pipeline_role, log_event_queue