# Security policy

## Reporting a vulnerability

Please do not open a public issue for security problems. Report them privately through GitHub's [private vulnerability reporting](../../security/advisories/new) for this repository. Include the affected file, what you observed and how to reproduce it.

Expect an acknowledgement within a week. Confirmed issues are fixed on `main`, and the report is credited unless you prefer otherwise.

## Scope

This repository is a hands-on lab that creates real, billable AWS resources in an account you control. Reports are welcome for:

- IAM permissions, network exposure or Kubernetes access that are broader than the lab needs
- Secrets, credentials or account data that the configuration or scripts could leak
- Pinned versions, images or actions with known vulnerabilities

Run the lab only in a disposable sandbox account, keep `operator_cidr` limited to your own `/32`, and tear it down when you finish.
