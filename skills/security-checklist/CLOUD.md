# Cloud and Infrastructure Security

Use this alongside [SKILL.md](SKILL.md) when the change touches deployment, IAM, networking, CI/CD, infrastructure-as-code, logging, CDN or backups.

## IAM

Grant the narrowest action on the narrowest resource.

```yaml
# Safe: read-only on one bucket
permissions: [s3:GetObject, s3:ListBucket]
resources:   [arn:aws:s3:::library-cover-images/*]

# Unsafe
permissions: ["s3:*"]
resources:   ["*"]
```

- [ ] No root or owner account used for day-to-day or production work.
- [ ] MFA on every privileged account.
- [ ] Services use roles or workload identity, not long-lived keys.
- [ ] Unused credentials removed; access reviewed periodically.

## Secrets in the cloud

- [ ] Secrets in a managed store (AWS Secrets Manager, GCP Secret Manager, the hosting platform's secret store), not baked into images or config.
- [ ] Database credentials rotate automatically; API keys rotate on a schedule.
- [ ] Secret access is audit-logged.

## Network

```hcl
# Safe: HTTPS from inside the VPC only
ingress { from_port = 443  to_port = 443  protocol = "tcp"  cidr_blocks = ["10.0.0.0/16"] }

# Unsafe: every port, the whole internet
ingress { from_port = 0  to_port = 65535  protocol = "tcp"  cidr_blocks = ["0.0.0.0/0"] }
```

- [ ] Databases are never publicly reachable (`publicly_accessible = false`).
- [ ] SSH and RDP only through a VPN or bastion.
- [ ] Storage buckets private by default, with explicit policies for what must be shared.
- [ ] Flow logs on.

## Logging and monitoring

- [ ] Auth failures and admin actions are logged, without sensitive data.
- [ ] Logs centralized, tamper-resistant, and retained as long as compliance requires.
- [ ] Alerts on anomalies (login spikes, permission changes, unusual egress).

## CI/CD

```yaml
permissions:
  contents: read            # least privilege for the workflow token
steps:
  - uses: actions/checkout@v4
  - run: <secret scan, e.g. trufflehog or gitleaks>
  - run: <dependency audit at high severity>
  - uses: aws-actions/configure-aws-credentials@v4
    with:
      role-to-assume: arn:aws:iam::<account>:role/deploy   # OIDC, no stored keys
```

- [ ] Cloud auth through OIDC, not stored long-lived secrets.
- [ ] Secret scanning and dependency audits run in the pipeline; container images scanned if used.
- [ ] Workflow token permissions minimal; third-party actions pinned.
- [ ] Branch protection and required review on the deploy branch.

## CDN and edge

- [ ] Security headers set at the edge: `X-Frame-Options: DENY` (or CSP `frame-ancestors`), `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, a restrictive `Permissions-Policy`.
- [ ] WAF with managed OWASP rules, rate limiting and bot protection where the provider offers them.
- [ ] TLS in strict mode end to end.

## Backups and recovery

- [ ] Automated backups with retention that meets requirements; point-in-time recovery for databases.
- [ ] Deletion protection on production data stores.
- [ ] Restores actually tested, with recovery point and recovery time objectives written down.

## Pre-deploy cloud checklist

- [ ] Least-privilege IAM, MFA, no root usage
- [ ] Secrets in a managed store with rotation
- [ ] No public databases or open ports; private buckets
- [ ] Logging, retention and alerting on
- [ ] OIDC deploys, secret scanning and audits in CI
- [ ] Edge headers, WAF and TLS configured
- [ ] Encryption at rest and in transit
- [ ] Backups tested
- [ ] Incident response plan and runbooks exist
