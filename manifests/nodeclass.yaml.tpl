apiVersion: karpenter.k8s.aws/v1
kind: EC2NodeClass
metadata:
  name: pdb-lab
spec:
  amiFamily: AL2023
  amiSelectorTerms:
    - id: "${AMI_ID}"
  role: "${NODE_ROLE}"
  subnetSelectorTerms:
    - tags:
        karpenter.sh/discovery: "${CLUSTER_NAME}"
  securityGroupSelectorTerms:
    - tags:
        karpenter.sh/discovery: "${CLUSTER_NAME}"
  metadataOptions:
    httpEndpoint: enabled
    httpTokens: required
    httpPutResponseHopLimit: 1
  tags:
    Project: "${CLUSTER_NAME}"
    Purpose: temporary-lab
