# Way of working

These are the steps to create the container, push the container to azure and run the container in azure:

1. When you are in the correct folder (container_notifications), build the Docker image locally and tag it
```bash
docker buildx build --platform=linux/amd64 -t bolia-dockers . #selecting linux/amd64 since it's going to be pushed to a Linux container in Azure.
```
2. Create a Resource Group and an Azure Container Registry (ACI) in Azure (done through the GUI here, and called them "Slack varslinger" and "varslinger"). This could have been done through the CLI, but have done it in the GUI for these specific resources.

3. Log in to Azure and to Azure Container Registry (ACI):
```bash
az login
az acr login --name varslinger
```
4. Tag and push the image you have built to Azure:
```bash
docker tag bolia-dockers varslinger.azurecr.io/bolia-dockers
docker push varslinger.azurecr.io/bolia-dockers:latest
```
4. Create an Azure Container App job:
```bash
az containerapp job create \
    --name bolia-container \
    --resource-group Slack-varslinger \
    --image varslinger.azurecr.io/bolia-dockers:latest \
    --cpu 1 \
    --memory 2 \
    --replica-timeout 3600 \
    --replica-retry-limit 500 \
    --registry-server varslinger.azurecr.io \
    --registry-username varslinger \
    --registry-password ENV_VAR_PASS \
    --environment varslinger \
    --trigger-type Schedule \
    --parallelism 1 \
    --replica-completion-count 1 \
    --cron-expression "0 10,16 * * *"
```

5. Create the Secret used in the Python script:
```bash
az containerapp secret set \
  --name bolia-container \
  --resource-group varslinger \
  --secrets slack-webhook-url=webhook_url(found under settings in your Slack_account)
  ```

6. Trigger the job manually if you want, and look at the jobs to check if the container has run successfully.
