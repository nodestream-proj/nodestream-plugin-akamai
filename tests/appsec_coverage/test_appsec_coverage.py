from nodestream_akamai.appsec_coverage.appsec_coverage import _extract_policy

hostname = {
    "configuration": {
        "id": 11111,
        "name": "ExampleCorp - WAF Security File",
        "version": 42,
    },
    "hasMatchTarget": True,
    "hostname": "other.example.com",
    "policyNames": ["Production"],
    "status": "covered",
}

covering_config = {
    "fileType": "RBAC",
    "id": 11111,
    "latestVersion": 43,
    "name": "ExampleCorp - WAF Security File",
    "productionHostnames": [
        "*.other.example.com",
        "*.other.other.example.com",
        "*.us1.other.example.com",
        "admin.example.com",
        "api-login.example.com",
        "apidocs.example.com",
        "blog.example.com",
        "campaigns.example.com",
        "other.example.com",
    ],
    "productionVersion": 42,
    "stagingVersion": 42,
    "targetProduct": "EXAMPLE",
    "policies": [{"policyId": "waf1_123456", "policyName": "Production"}],
}


def test__extract_policy():

    assert _extract_policy(covering_config, hostname, "Production") == {
        "hostname": "other.example.com",
        "policy_name": "Production",
        "policyId": "waf1_123456",
    }
