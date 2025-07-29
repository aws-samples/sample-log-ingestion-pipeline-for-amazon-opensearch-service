#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdk.cloudwatch_stack import CloudWatchStack
from cdk.opensearch_stack import OpensearchStack
from cdk.ingestion_stack import IngestionStack
from cdk.pipeline_stack import PipelineStack

print("📍 CDK region in use:", os.environ.get("CDK_DEFAULT_REGION"))


app = cdk.App()
cloudwatch_stack = CloudWatchStack(app, "CdkCloudWatchStack")
ingestion_stack = IngestionStack(app, "CdkIngestionStack")

opensearch_stack = OpensearchStack(app,"CdkOpensearchStack", cloudwatch_stack, ingestion_stack)
opensearch_stack.add_dependency(cloudwatch_stack)
opensearch_stack.add_dependency(ingestion_stack)

pipeline_stack = PipelineStack(app, "CdkPipelineStack", opensearch_stack, 
                cloudwatch_stack, ingestion_stack)

pipeline_stack.add_dependency(opensearch_stack)


app.synth()
