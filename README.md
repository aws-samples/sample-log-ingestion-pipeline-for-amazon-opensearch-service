
# Amazon OpenSearch Service 101: A Success Blueprint for OpenSearch Logging

This is a Python CDK Project which deploys an [Amazon OpenSearch Service Domain](https://aws.amazon.com/opensearch-service/) and associated components. This project demonstrates event based data ingestion into the OpenSearch Service Domain in a no code approach using [Amazon OpenSearch Ingeestion Pipelines](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/ingestion.html).

The following architecture diagram illustrates:

![Ingestion Architecture](/images/ingestion_architecture_diagram.jpg)

1. The data source or the log source produces logs into the S3 Bucket.

2. S3 creates an event notification (for ObjectCreate events) in the SQS Queue.

3. OpenSearch Ingestion Pipeline polls Amazon SQS Queue for events and then receive the S3 File events.

4. OpenSearch Ingestion Pipeline then parses and ingests the logs (using Bulk API) to the Opensearch Service Domain.

## Deploy AWS CDK stacks

The deployment is automated using AWS Cloud Development Kit (AWS CDK) and comprises of the following steps:

1. Clone the Gitlab repo. Once the repo is cloned, create a virual environment and install the python dependencies

```
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
```

2. After installing the dependencies, ensure your AWS CLI is configured with the correct credentials and region for deployment. Run the following command and provide:

- Your AWS access key ID
- Your AWS secret access key
- The AWS Region where you want to deploy (e.g., us-east-1)

``` 
aws configure
 ```

This is required for CDK to authenticate and deploy resources into your AWS account.

3. Update the following the environment variables in cdk.json
    - domain_name : The name of OpenSearch Domain to be created in your AWS Account
    - user_name: The username for the internal master user to be created within the OpenSearch Domain
    - user_password: The password for the internal master user.

4. Bootstrap the CDK Stack and initiate the deployment. Replace `123456789012` with your AWS account number, `us-east-1` with the AWS Region to which you want deploy the solution (use the same region you specified in step 2 during aws configure).

```
cdk bootstrap 123456789012/us-east-1
cdk deploy --all
```

The whole process takes about **30-45 minutes** to complete.


## Create the OpenSearch Objects

Once the CDK Stack Deployment is complete, please follow the below steps : 

1. Navigate to the Amazon OpenSearch Service Console in the deployed region within your AWS Account and select the domain which us created.

2. Click on the **OpenSearch Dashboards URL** after which a login prompt would be displayed. Enter the user credentials which were provided in `cdk.json`

3. After a successful login, The OpenSearch Dashboards console will be displayed. In case of tenant selection prompt, select the **Global** tenant.

4. Please refer to the below image and navigate to the **Security** options.

![OpenSearch Dashboard Options](/images/options.png)

5. Within the Security options, navigate to the **Roles** option and select the **all_access** role.

![OpenSearch All Access Role](/images/all_access.png)

6. Within all_access role page, navigate to **mapped_users** and select the **Mange Mapping** option. Select the **Add another backend role** option within **Backend roles** and add the IAM Role ARN - ```arn:aws:iam::<AWS Account ID>:role/apache-log-ingestion-<Domain Name>```. Confirm by clicking the Map option.
Replace ```AWS Account ID```  with your actual AWS Account ID and ```Domain Name``` with domain name you provided in cdk.json.

![OpenSearch Role Mapping](/images/iam_role_mapping.png)

7. Once the above step is completed, navigate to the **Dev Tools** Console.

![OpenSearch Dev Tools](/images/dev_tools_console.png)

8. Copy the contents of the file ```index_template.txt``` within the ```opensearch_object``` directory and paste in the Dev Console and click on the ```play``` button to submit the request.

![OpenSearch Index Template](/images/index_template_creation.png)

9. Once the above step is completed, navigate to the **Dashboard Management** Console.

![OpenSearch Dev Tools](/images/dashboard_management.png)

10. Within the Dashboard Management Console, select the **Saved Objects** option and click on the **Import** option. Within the import saved objects options, click on import and select the ```apache_access_log_dashboard.ndjson``` file within the ```opensearch_object``` directory. 

Once, done select the **Check for existing objects** configuration. Further select the **Automatically overwrite conflicts** and then select the import option. 

![Importing Saved Objects](/images/saved_objects_import.png)

## Final Steps

Once the appropriate OpenSearch Objects are created, you can proceed with the data ingestion. Naviagte to the S3 bcuket Console and upload the data file ```apache_access_log.gz``` to the S3 Bucket ```opensearch-logging-blog-{AWS Account ID}-{Domain Name}```. The file can be uploaded in any prefix.
Replace ```AWS Account ID``` with your actual AWS Account ID and ```Domain Name``` with domain name you provided in cdk.json.

After few minutes, navigate to the ```Discover``` Tab within ```OpenSeacrh Dashboards``` within which you will find that the data is ingested. Ensure that the ```apache*``` index pattern is selected.

![Discover Tab](/images/discover_tab.png)

You can then navigate to the ```Dashboards``` Tab and select the ```Apache Log Dashboard```. The dashboard would be populated by the data and visuals should be displayed.

![Apache Log Dashboard](/images/apache_log_dashboard.png)


