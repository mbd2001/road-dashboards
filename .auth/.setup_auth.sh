#!/bin/bash

if ! command -v "vault" &> /dev/null; then
  echo "vault does not exist, skipping credentials setup..."
  return 0
else
  echo "Setting up credentials."
fi

# setup Vault credentials
export VAULT_ADDR="https://vault.sddc.mobileye.com"
export VAULT_FORMAT=json
export VAULT_ROLE_ID=${VAULT_ROLE_ID}  # we get this from CI/CD variables
export VAULT_SECRET_ID=${VAULT_SECRET_ID} # we get this from CI/CD variables
export VAULT_TOKEN=$(vault write auth/approle/login role_id="${VAULT_ROLE_ID}" secret_id="${VAULT_SECRET_ID}" | yq4 .auth.client_token)

# setup AWS credentials
export ARN=$(vault kv get -format=json algo-road/aws_credentials | yq4 .data.data.aws_role)
export AWS=$(vault write cloud/aws/sts/algo_road ttl=12h role_arn=${ARN} credential_type=assumed_role | yq4 .data)
export AWS_ACCESS_KEY_ID=$(echo ${AWS} | yq4 .access_key)
export AWS_SECRET_ACCESS_KEY=$(echo ${AWS} | yq4 .secret_key)
export AWS_SESSION_TOKEN=$(echo ${AWS} | yq4 .security_token)
export AWS_DEFAULT_REGION="us-east-1"

# setup Artifactory credentials
export ARTIFACTORY_VARS=$(vault kv get -format=json algo-road/artifactory_token)
export ARTIFACTORY_TOKEN=$(echo $ARTIFACTORY_VARS | yq4 .data.data.token)

# setup Faceless User credentials
FACELESS_USER_JSON=$(vault kv get algo-road/faceless_user_credentials)
export FACELESS_ONPREM_USER=$(echo ${FACELESS_USER_JSON} | yq4 .data.data.onprem_username)
export FACELESS_AZURE_USER=$(echo ${FACELESS_USER_JSON} | yq4 .data.data.azure_username)
export FACELESS_PASS=$(echo ${FACELESS_USER_JSON} | yq4 .data.data.password)

# setup DE credentials
export DE_TOKEN=$(vault kv get -format=json algo-road/de-token | yq4 .data.data.token)

# setup MeeZeh credentials
export MZ_FACELESS_USERNAME=$(echo ${FACELESS_USER_JSON} | yq4 .data.data.azure_username)@mobileye.com
export MZ_FACELESS_PASSWORD=$(echo ${FACELESS_USER_JSON} | yq4 .data.data.password)
export MZ_FACELESS_ENABLED=true