import json

rule_tree_488011 = json.loads(
    """
{
  "accountId": "0-00AA",
  "contractId": "C-8M9LB",
  "groupId": "27552",
  "propertyId": "488011",
  "propertyName": "e.example.com",
  "propertyVersion": 2,
  "etag": "50ca05b51aee65ba4a065f1a12b16fbb4f294c5f",
  "rules": {
    "name": "default",
    "children": [
      {
        "name": "Content Compression",
        "children": [],
        "behaviors": [
          {
            "name": "gzipResponse",
            "options": {
              "behavior": "ALWAYS"
            }
          }
        ],
        "criteria": [
          {
            "name": "contentType",
            "options": {
              "matchCaseSensitive": false,
              "matchOperator": "IS_ONE_OF",
              "matchWildcard": true,
              "values": [
                "text/*",
                "application/javascript",
                "application/x-javascript",
                "application/x-javascript*",
                "application/json",
                "application/x-json",
                "application/*+json",
                "application/*+xml",
                "application/text",
                "application/vnd.microsoft.icon",
                "application/vnd-ms-fontobject",
                "application/x-font-ttf",
                "application/x-font-opentype",
                "application/x-font-truetype",
                "application/xmlfont/eot",
                "application/xml",
                "font/opentype",
                "font/otf",
                "font/eot",
                "image/svg+xml",
                "image/vnd.microsoft.icon"
              ]
            }
          }
        ],
        "criteriaMustSatisfy": "all"
      },
      {
        "name": "Static Content",
        "children": [],
        "behaviors": [
          {
            "name": "caching",
            "options": {
              "behavior": "MAX_AGE",
              "mustRevalidate": false,
              "ttl": "1d"
            }
          },
          {
            "name": "prefetch",
            "options": {
              "enabled": false
            }
          },
          {
            "name": "prefetchable",
            "options": {
              "enabled": true
            }
          }
        ],
        "criteria": [
          {
            "name": "fileExtension",
            "options": {
              "matchCaseSensitive": false,
              "matchOperator": "IS_ONE_OF",
              "values": [
                "aif",
                "aiff",
                "au",
                "avi",
                "bin",
                "bmp",
                "cab",
                "carb",
                "cct",
                "cdf",
                "class",
                "css",
                "doc",
                "dcr",
                "dtd",
                "exe",
                "flv",
                "gcf",
                "gff",
                "gif",
                "grv",
                "hdml",
                "hqx",
                "ico",
                "ini",
                "jpeg",
                "jpg",
                "js",
                "mov",
                "mp3",
                "nc",
                "pct",
                "pdf",
                "png",
                "ppc",
                "pws",
                "swa",
                "swf",
                "txt",
                "vbs",
                "w32",
                "wav",
                "wbmp",
                "wml",
                "wmlc",
                "wmls",
                "wmlsc",
                "xsd",
                "zip",
                "webp",
                "jxr",
                "hdp",
                "wdp",
                "pict",
                "tif",
                "tiff",
                "mid",
                "midi",
                "ttf",
                "eot",
                "woff",
                "woff2",
                "otf",
                "svg",
                "svgz",
                "jar",
                "jp2"
              ]
            }
          }
        ],
        "criteriaMustSatisfy": "any"
      },
      {
        "name": "Dynamic Content",
        "children": [],
        "behaviors": [
          {
            "name": "downstreamCache",
            "options": {
              "behavior": "TUNNEL_ORIGIN"
            }
          }
        ],
        "criteria": [
          {
            "name": "cacheability",
            "options": {
              "matchOperator": "IS_NOT",
              "value": "CACHEABLE"
            }
          }
        ],
        "criteriaMustSatisfy": "any"
      },
      {
        "name": "Redirect to /features/",
        "children": [],
        "behaviors": [
          {
            "name": "redirect",
            "options": {
              "mobileDefaultChoice": "DEFAULT",
              "destinationProtocol": "HTTPS",
              "destinationHostname": "OTHER",
              "destinationPath": "OTHER",
              "queryString": "APPEND",
              "responseCode": 302,
              "destinationPathOther": "/design/",
              "destinationHostnameOther": "example.com"
            }
          }
        ],
        "criteria": [],
        "criteriaMustSatisfy": "all"
      },
      {
        "name": "www Redirect",
        "children": [],
        "behaviors": [
          {
            "name": "redirect",
            "options": {
              "mobileDefaultChoice": "DEFAULT",
              "destinationProtocol": "HTTPS",
              "destinationHostname": "OTHER",
              "destinationPath": "SAME_AS_REQUEST",
              "queryString": "APPEND",
              "responseCode": 302,
              "destinationHostnameOther": "d.example.com"
            }
          }
        ],
        "criteria": [
          {
            "name": "hostname",
            "options": {
              "matchOperator": "IS_ONE_OF",
              "values": [
                "w.example.com"
              ]
            }
          }
        ],
        "criteriaMustSatisfy": "all"
      }
    ],
    "behaviors": [
      {
        "name": "origin",
        "options": {
          "originType": "NET_STORAGE",
          "netStorage": {
            "downloadDomainName": "example.download.akamai.com",
            "cpCode": 391386,
            "g2oToken": null
          },
          "useUniqueCacheKey": false
        }
      },
      {
        "name": "cpCode",
        "options": {
          "value": {
            "id": 640994,
            "description": "Future13",
            "products": [
              "Alta",
              "Fresca"
            ],
            "createdDate": 1510172296000,
            "name": "Future13"
          }
        }
      },
      {
        "name": "caching",
        "options": {
          "behavior": "MAX_AGE",
          "mustRevalidate": false,
          "ttl": "10m"
        }
      },
      {
        "name": "sureRoute",
        "options": {
          "enabled": false
        }
      },
      {
        "name": "tieredDistribution",
        "options": {
          "enabled": false
        }
      },
      {
        "name": "enhancedAkamaiProtocol",
        "options": {
          "display": ""
        }
      },
      {
        "name": "prefetch",
        "options": {
          "enabled": true
        }
      },
      {
        "name": "allowPost",
        "options": {
          "allowWithoutContentLength": false,
          "enabled": true
        }
      },
      {
        "name": "report",
        "options": {
          "logAcceptLanguage": false,
          "logCookies": "OFF",
          "logCustomLogField": false,
          "logHost": true,
          "logReferer": true,
          "logUserAgent": true,
          "logEdgeIP": false,
          "logXForwardedFor": false
        }
      },
      {
        "name": "realUserMonitoring",
        "options": {
          "enabled": true
        }
      },
      {
        "name": "cacheKeyQueryParams",
        "options": {
          "behavior": "IGNORE_ALL"
        }
      },
      {
        "name": "cacheError",
        "options": {
          "enabled": true,
          "ttl": "30s",
          "preserveStale": true
        }
      }
    ],
    "options": {
      "is_secure": true
    },
    "variables": []
  },
  "warnings": [
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/generic_behavior_issue.all_methods_on_ps",
      "errorLocation": "#/rules/behaviors/7",
      "detail": "warning 1 detail"
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/generic_behavior_issue.rum_eol",
      "errorLocation": "#/rules/behaviors/9",
      "detail": "<strong> Important </strong>: Real User Monitoring reports are no longer available. You can continue to use RUM for Adaptive Acceleration, but we <strong>recommend switching to mPulse</strong>."
    },
    {
      "title": "Unstable rule format",
      "type": "https://problems.luna.akamaiapis.net/papi/v0/unstable_rule_format",
      "detail": "This property is using `latest` rule format, which is designed to reflect interface changes immediately. We suggest converting the property to a stable rule format such as `v2025-02-18` to minimize the risk of interface changes breaking your API client program.",
      "currentRuleFormat": "latest",
      "suggestedRuleFormat": "v2025-02-18"
    }
  ],
  "ruleFormat": "latest",
  "comments": "[SRE-3202] - Redirect for w.example.com to https://d.example.com/"
}
"""
)
rule_tree_643957 = json.loads(
    """
{
  "accountId": "0-00AA",
  "contractId": "C-19XSR8V",
  "groupId": "124752",
  "propertyId": "643957",
  "propertyName": "community-e2e",
  "propertyVersion": 142,
  "etag": "6a3c9f97c2dbe160febfc9264a1850cf4114a3f7",
  "rules": {
    "name": "default",
    "children": [
      {
        "name": "Edge Scape",
        "children": [],
        "behaviors": [
          {
            "name": "edgeScape",
            "options": {
              "enabled": true
            }
          }
        ],
        "criteria": [],
        "criteriaMustSatisfy": "all",
        "templateLink": "/platformtoolkit/service/ruletemplate/74368506/1?accountId=0-00AA&gid=124752&ck=18.9.0.2"
      },
      {
        "name": "Preprod: Safelisting by IP",
        "children": [],
        "behaviors": [
          {
            "name": "denyAccess",
            "options": {
              "enabled": true,
              "reason": "deny-by-ip"
            }
          }
        ],
        "criteria": [
          {
            "name": "clientIp",
            "options": {
              "matchOperator": "IS_NOT_ONE_OF",
              "useHeaders": true,
              "values": [
                "10.10.10.0/21"
              ]
            }
          }
        ],
        "criteriaMustSatisfy": "all",
        "comments": "List of IP ranges that are allowed in preprod."
      },
      {
        "name": "Embargo Geo Blocking",
        "children": [
          {
            "name": "Log Delivery",
            "children": [],
            "behaviors": [
              {
                "name": "setVariable",
                "options": {
                  "extractLocation": "EDGESCAPE",
                  "locationId": "COUNTRY_CODE",
                  "transform": "NONE",
                  "valueSource": "EXTRACT",
                  "variableName": "PMUSER_COUNTRY"
                }
              },
              {
                "name": "report",
                "options": {
                  "customLogField": "{{user.PMUSER_COUNTRY}}",
                  "logAcceptLanguage": false,
                  "logCookies": "OFF",
                  "logCustomLogField": true,
                  "logHost": true,
                  "logReferer": false,
                  "logUserAgent": false,
                  "logEdgeIP": false,
                  "logXForwardedFor": false
                }
              }
            ],
            "criteria": [],
            "criteriaMustSatisfy": "all",
            "templateLink": "/platformtoolkit/service/ruletemplate/93924560/1?accountId=0-00AA&gid=124752&ck=18.8"
          }
        ],
        "behaviors": [
          {
            "name": "requestControl",
            "options": {
              "cloudletPolicy": {
                "id": 32773,
                "name": "Embargo_Geo_Blocking"
              },
              "enableBranded403": false,
              "enabled": true,
              "isSharedPolicy": false
            }
          }
        ],
        "criteria": [
          {
            "name": "userLocation",
            "options": {
              "checkIps": "BOTH",
              "countryValues": [
                "CU",
                "SD",
                "SY",
                "IR",
                "KP"
              ],
              "field": "COUNTRY",
              "matchOperator": "IS_ONE_OF",
              "useOnlyFirstXForwardedForIp": false
            }
          },
          {
            "name": "userLocation",
            "options": {
              "checkIps": "BOTH",
              "field": "REGION",
              "matchOperator": "IS_ONE_OF",
              "regionValues": [
                "UA-CRIMEA"
              ],
              "useOnlyFirstXForwardedForIp": false
            }
          }
        ],
        "criteriaMustSatisfy": "any",
        "templateLink": "/platformtoolkit/service/ruletemplate/93924560/1?accountId=0-00AA&gid=124752&ck=18.8"
      },
      {
        "name": "Offload",
        "children": [
          {
            "name": "Static Objects",
            "children": [],
            "behaviors": [
              {
                "name": "caching",
                "options": {
                  "behavior": "MAX_AGE",
                  "mustRevalidate": false,
                  "ttl": "1d"
                }
              },
              {
                "name": "prefreshCache",
                "options": {
                  "enabled": true,
                  "prefreshval": 90
                }
              },
              {
                "name": "prefetchable",
                "options": {
                  "enabled": true
                }
              }
            ],
            "criteria": [
              {
                "name": "fileExtension",
                "options": {
                  "matchCaseSensitive": false,
                  "matchOperator": "IS_ONE_OF",
                  "values": [
                    "aif",
                    "aiff",
                    "au",
                    "avi",
                    "bin",
                    "bmp",
                    "cab",
                    "carb",
                    "cct",
                    "cdf",
                    "class",
                    "doc",
                    "dcr",
                    "dtd",
                    "exe",
                    "flv",
                    "gcf",
                    "gff",
                    "gif",
                    "grv",
                    "hdml",
                    "hqx",
                    "ico",
                    "ini",
                    "jpeg",
                    "jpg",
                    "mov",
                    "mp3",
                    "nc",
                    "pct",
                    "pdf",
                    "png",
                    "ppc",
                    "pws",
                    "swa",
                    "swf",
                    "txt",
                    "vbs",
                    "w32",
                    "wav",
                    "wbmp",
                    "wml",
                    "wmlc",
                    "wmls",
                    "wmlsc",
                    "xsd",
                    "zip",
                    "pict",
                    "tif",
                    "tiff",
                    "mid",
                    "midi",
                    "ttf",
                    "eot",
                    "woff",
                    "woff2",
                    "otf",
                    "svg",
                    "svgz",
                    "webp",
                    "jxr",
                    "jar",
                    "jp2"
                  ]
                }
              }
            ],
            "criteriaMustSatisfy": "any",
            "comments": "Overrides the default caching behavior for images, music, and similar objects that are cached on the edge server. Because these object types are static, the TTL is long."
          },
          {
            "name": "Uncacheable Responses",
            "children": [],
            "behaviors": [
              {
                "name": "downstreamCache",
                "options": {
                  "behavior": "TUNNEL_ORIGIN"
                }
              }
            ],
            "criteria": [
              {
                "name": "cacheability",
                "options": {
                  "matchOperator": "IS_NOT",
                  "value": "CACHEABLE"
                }
              }
            ],
            "criteriaMustSatisfy": "all",
            "comments": "Overrides the default downstream caching behavior for uncacheable object types. Instructs the edge server to pass Cache-Control and/or Expire headers from the origin to the client."
          }
        ],
        "behaviors": [
          {
            "name": "caching",
            "options": {
              "behavior": "NO_STORE"
            }
          },
          {
            "name": "cacheError",
            "options": {
              "enabled": true,
              "preserveStale": true,
              "ttl": "10s"
            }
          },
          {
            "name": "downstreamCache",
            "options": {
              "behavior": "TUNNEL_ORIGIN"
            }
          }
        ],
        "criteria": [],
        "criteriaMustSatisfy": "all",
        "comments": "Controls caching, which offloads traffic away from the origin. Most objects types are not cached. However, the child rules override this behavior for certain subsets of requests."
      },
      {
        "name": "Performance",
        "children": [
          {
            "name": "Compressible Objects",
            "children": [],
            "behaviors": [
              {
                "name": "gzipResponse",
                "options": {
                  "behavior": "ALWAYS"
                }
              }
            ],
            "criteria": [
              {
                "name": "contentType",
                "options": {
                  "matchCaseSensitive": false,
                  "matchOperator": "IS_ONE_OF",
                  "matchWildcard": true,
                  "values": [
                    "text/*",
                    "application/javascript",
                    "application/x-javascript",
                    "application/x-javascript*",
                    "application/json",
                    "application/x-json",
                    "application/*+json",
                    "application/*+xml",
                    "application/text",
                    "application/vnd.microsoft.icon",
                    "application/vnd-ms-fontobject",
                    "application/x-font-ttf",
                    "application/x-font-opentype",
                    "application/x-font-truetype",
                    "application/xmlfont/eot",
                    "application/xml",
                    "font/opentype",
                    "font/otf",
                    "font/eot",
                    "image/svg+xml",
                    "image/vnd.microsoft.icon"
                  ]
                }
              }
            ],
            "criteriaMustSatisfy": "all",
            "comments": "Compresses content to improve performance of clients with slow connections. Applies Last Mile Acceleration to requests when the returned object supports gzip compression."
          }
        ],
        "behaviors": [
          {
            "name": "enhancedAkamaiProtocol",
            "options": {
              "display": ""
            }
          },
          {
            "name": "http2",
            "options": {
              "enabled": ""
            }
          },
          {
            "name": "allowTransferEncoding",
            "options": {
              "enabled": true
            }
          },
          {
            "name": "removeVary",
            "options": {
              "enabled": true
            }
          },
          {
            "name": "prefetch",
            "options": {
              "enabled": true
            }
          }
        ],
        "criteria": [],
        "criteriaMustSatisfy": "all",
        "comments": "Improves the performance of delivering objects to end users. Behaviors in this rule are applied to all requests as appropriate."
      },
      {
        "name": "Redirect 401 to Root",
        "children": [],
        "behaviors": [
          {
            "name": "modifyOutgoingResponseHeader",
            "options": {
              "action": "ADD",
              "standardAddHeaderName": "OTHER",
              "headerValue": "https://{{builtin.AK_HOST}}/community",
              "customHeaderName": "Location"
            }
          },
          {
            "name": "responseCode",
            "options": {
              "statusCode": 302
            }
          }
        ],
        "criteria": [
          {
            "name": "matchResponseCode",
            "options": {
              "matchOperator": "IS_ONE_OF",
              "values": [
                "401"
              ]
            }
          },
          {
            "name": "path",
            "options": {
              "matchOperator": "MATCHES_ONE_OF",
              "values": [
                "/community/s/auth/saml/login"
              ],
              "matchCaseSensitive": false,
              "normalize": false
            }
          }
        ],
        "criteriaMustSatisfy": "all",
        "comments": "Redirects a SAML 401 not authorized to the root of the community"
      },
      {
        "name": "Redirect to HTTPS",
        "children": [],
        "behaviors": [
          {
            "name": "redirect",
            "options": {
              "queryString": "APPEND",
              "responseCode": 301,
              "destinationHostname": "SAME_AS_REQUEST",
              "destinationPath": "SAME_AS_REQUEST",
              "destinationProtocol": "HTTPS",
              "mobileDefaultChoice": "DEFAULT"
            }
          }
        ],
        "criteria": [
          {
            "name": "requestProtocol",
            "options": {
              "value": "HTTP"
            }
          }
        ],
        "criteriaMustSatisfy": "all",
        "comments": "Redirect to the same URL on HTTPS protocol, issuing a 301 response code (Moved Permanently). You may change the response code to 302 if needed."
      },
      {
        "name": "Outgoing: XFF Header",
        "children": [],
        "behaviors": [
          {
            "name": "modifyOutgoingRequestHeader",
            "options": {
              "action": "MODIFY",
              "standardModifyHeaderName": "OTHER",
              "newHeaderValue": "{{builtin.AK_CLIENT_REAL_IP}}",
              "avoidDuplicateHeaders": true,
              "customHeaderName": "X-Forwarded-For"
            }
          }
        ],
        "criteria": [
          {
            "name": "requestType",
            "options": {
              "matchOperator": "IS",
              "value": "CLIENT_REQ"
            }
          }
        ],
        "criteriaMustSatisfy": "all"
      },
      {
        "name": "Bot Verification Pages",
        "children": [],
        "behaviors": [
          {
            "name": "origin",
            "options": {
              "originType": "NET_STORAGE",
              "netStorage": {
                "downloadDomainName": "sgds.download.akamai.com",
                "cpCode": 856619,
                "g2oToken": null
              },
              "useUniqueCacheKey": false
            }
          },
          {
            "name": "caching",
            "options": {
              "behavior": "MAX_AGE",
              "mustRevalidate": true,
              "ttl": "12h"
            }
          }
        ],
        "criteria": [
          {
            "name": "filename",
            "options": {
              "matchOperator": "IS_ONE_OF",
              "values": [
                "BingSiteAuth.xml",
                "google00bd30f85153dba5.html",
                "sitemap-purge.xml",
                "sitemap-purge-1.xml",
                "sitemap-purge-2.xml",
                "sitemap-purge-3.xml",
                "sitemap-purge-4.xml",
                "sitemap-purge-5.xml",
                "sitemap-purge-6.xml",
                "sitemap-purge-7.xml",
                "sitemap-purge-8.xml",
                "sitemap-purge-9.xml",
                "sitemap-purge-10.xml",
                "sitemap-purge-11.xml",
                "sitemap-purge-12.xml"
              ],
              "matchCaseSensitive": false
            }
          }
        ],
        "criteriaMustSatisfy": "all"
      },
      {
        "name": "Sitemap",
        "children": [],
        "behaviors": [
          {
            "name": "rewriteUrl",
            "options": {
              "behavior": "REPLACE",
              "keepQueryString": true,
              "match": "/community/",
              "targetPath": "/cg/e.example.com/",
              "matchMultiple": true
            }
          },
          {
            "name": "origin",
            "options": {
              "originType": "CUSTOMER",
              "hostname": "s.example.com",
              "forwardHostHeader": "ORIGIN_HOSTNAME",
              "cacheKeyHostname": "ORIGIN_HOSTNAME",
              "compress": true,
              "enableTrueClientIp": true,
              "originCertificate": "",
              "verificationMode": "CUSTOM",
              "ports": "",
              "httpPort": 80,
              "httpsPort": 443,
              "trueClientIpHeader": "True-Client-IP",
              "trueClientIpClientSetting": false,
              "originSni": true,
              "customValidCnValues": [
                "{{Origin Hostname}}",
                "{{Forward Host Header}}"
              ],
              "originCertsToHonor": "STANDARD_CERTIFICATE_AUTHORITIES",
              "standardCertificateAuthorities": [
                "akamai-permissive"
              ],
              "minTlsVersion": "DYNAMIC",
              "ipVersion": "IPV4",
              "useUniqueCacheKey": false
            }
          },
          {
            "name": "modifyOutgoingResponseHeader",
            "options": {
              "action": "ADD",
              "standardAddHeaderName": "OTHER",
              "headerValue": "true",
              "customHeaderName": "X-Sitemap-File"
            }
          }
        ],
        "criteria": [
          {
            "name": "path",
            "options": {
              "matchOperator": "MATCHES_ONE_OF",
              "values": [
                "/community/sitemap*.xml"
              ],
              "matchCaseSensitive": false,
              "normalize": false
            }
          }
        ],
        "criteriaMustSatisfy": "all"
      },
      {
        "name": "robots.txt",
        "children": [],
        "behaviors": [
          {
            "name": "rewriteUrl",
            "options": {
              "behavior": "REWRITE",
              "targetUrl": "/cg/e.example.com/robots.txt"
            }
          },
          {
            "name": "origin",
            "options": {
              "originType": "CUSTOMER",
              "hostname": "s.example.com",
              "forwardHostHeader": "ORIGIN_HOSTNAME",
              "cacheKeyHostname": "ORIGIN_HOSTNAME",
              "compress": true,
              "enableTrueClientIp": true,
              "originCertificate": "",
              "verificationMode": "CUSTOM",
              "ports": "",
              "httpPort": 80,
              "httpsPort": 443,
              "trueClientIpHeader": "True-Client-IP",
              "trueClientIpClientSetting": false,
              "originSni": true,
              "customValidCnValues": [
                "{{Origin Hostname}}",
                "{{Forward Host Header}}"
              ],
              "originCertsToHonor": "STANDARD_CERTIFICATE_AUTHORITIES",
              "standardCertificateAuthorities": [
                "akamai-permissive"
              ],
              "minTlsVersion": "DYNAMIC",
              "ipVersion": "IPV4",
              "useUniqueCacheKey": false
            }
          },
          {
            "name": "modifyOutgoingResponseHeader",
            "options": {
              "action": "ADD",
              "standardAddHeaderName": "OTHER",
              "headerValue": "true",
              "customHeaderName": "X-robots-File"
            }
          }
        ],
        "criteria": [
          {
            "name": "path",
            "options": {
              "matchOperator": "MATCHES_ONE_OF",
              "values": [
                "/robots.txt"
              ],
              "matchCaseSensitive": false,
              "normalize": false
            }
          }
        ],
        "criteriaMustSatisfy": "all",
        "comments": "This is to proxy robots.txt to our AWS CDN for sitemap and robots."
      },
      {
        "name": "Khoros Origin",
        "children": [
          {
            "name": "Remove IUS Cookie",
            "children": [
              {
                "name": "Send Filtered Cookie request forward",
                "children": [],
                "behaviors": [
                  {
                    "name": "modifyOutgoingRequestHeader",
                    "options": {
                      "action": "ADD",
                      "customHeaderName": "Cookie",
                      "headerValue": "{{user.PMUSER_COOKIE_FILT}}",
                      "standardAddHeaderName": "OTHER"
                    }
                  }
                ],
                "criteria": [
                  {
                    "name": "matchVariable",
                    "options": {
                      "matchOperator": "IS_NOT_EMPTY",
                      "variableName": "PMUSER_COOKIE_FILT"
                    }
                  }
                ],
                "criteriaMustSatisfy": "all",
                "templateLink": "/platformtoolkit/service/ruletemplate/111111111/1?accountId=0-00AA&gid=124752&ck=19.7.1.1"
              }
            ],
            "behaviors": [
              {
                "name": "setVariable",
                "options": {
                  "caseSensitive": true,
                  "extractLocation": "CLIENT_REQUEST_HEADER",
                  "globalSubstitution": true,
                  "headerName": "Cookie",
                  "regex": "^(example1|example2)...(.*)",
                  "replacement": "",
                  "transform": "SUBSTITUTE",
                  "valueSource": "EXTRACT",
                  "variableName": "PMUSER_COOKIE_FILT"
                }
              },
              {
                "name": "modifyOutgoingRequestHeader",
                "options": {
                  "action": "DELETE",
                  "customHeaderName": "Cookie",
                  "standardDeleteHeaderName": "OTHER"
                }
              }
            ],
            "criteria": [
              {
                "name": "requestCookie",
                "options": {
                  "cookieName": "example2*",
                  "matchCaseSensitiveName": true,
                  "matchOperator": "EXISTS",
                  "matchWildcardName": false
                }
              },
              {
                "name": "requestCookie",
                "options": {
                  "cookieName": "example1*",
                  "matchOperator": "EXISTS",
                  "matchWildcardName": false,
                  "matchCaseSensitiveName": true
                }
              }
            ],
            "criteriaMustSatisfy": "any",
            "templateLink": "/platformtoolkit/service/ruletemplate/152654703/1?accountId=0-00AA&gid=124752&ck=19.7.1.1"
          },
          {
            "name": "Turnaway Page for 5xx error",
            "children": [
              {
                "name": "Check for browser traffic",
                "children": [],
                "behaviors": [
                  {
                    "name": "failAction",
                    "options": {
                      "enabled": true,
                      "actionType": "REDIRECT",
                      "redirectHostnameType": "ALTERNATE",
                      "redirectCustomPath": true,
                      "redirectMethod": 302,
                      "modifyProtocol": true,
                      "redirectHostname": "s.example.com",
                      "redirectPath": "/500.html",
                      "preserveQueryString": true,
                      "protocol": "HTTPS"
                    }
                  }
                ],
                "criteria": [
                  {
                    "name": "path",
                    "options": {
                      "matchOperator": "DOES_NOT_MATCH_ONE_OF",
                      "values": [
                        "/community/s/*"
                      ],
                      "matchCaseSensitive": false,
                      "normalize": false
                    }
                  }
                ],
                "criteriaMustSatisfy": "all"
              }
            ],
            "behaviors": [],
            "criteria": [
              {
                "name": "matchResponseCode",
                "options": {
                  "matchOperator": "IS_ONE_OF",
                  "values": [
                    "500",
                    "502",
                    "504"
                  ]
                }
              },
              {
                "name": "originTimeout",
                "options": {
                  "matchOperator": "ORIGIN_TIMED_OUT"
                }
              }
            ],
            "criteriaMustSatisfy": "any",
            "comments": "Turnaway page for Origin 5xx"
          }
        ],
        "behaviors": [
          {
            "name": "modifyOutgoingRequestHeader",
            "options": {
              "action": "MODIFY",
              "standardModifyHeaderName": "OTHER",
              "newHeaderValue": "vWZuU?2kax",
              "avoidDuplicateHeaders": true,
              "customHeaderName": "X-example-Header"
            }
          },
          {
            "name": "modifyOutgoingRequestHeader",
            "options": {
              "action": "MODIFY",
              "standardModifyHeaderName": "OTHER",
              "newHeaderValue": "{{builtin.AK_HOST}}",
              "avoidDuplicateHeaders": true,
              "customHeaderName": "X-Forwarded-Host"
            }
          },
          {
            "name": "modifyOutgoingRequestHeader",
            "options": {
              "action": "MODIFY",
              "standardModifyHeaderName": "OTHER",
              "newHeaderValue": "https",
              "avoidDuplicateHeaders": true,
              "customHeaderName": "X-Forwarded-Proto"
            }
          },
          {
            "name": "origin",
            "options": {
              "cacheKeyHostname": "ORIGIN_HOSTNAME",
              "compress": true,
              "customValidCnValues": [
                "{{Origin Hostname}}",
                "{{Forward Host Header}}",
                "secure01.lithium.com",
                "secure10.lithium.com"
              ],
              "enableTrueClientIp": true,
              "forwardHostHeader": "ORIGIN_HOSTNAME",
              "hostname": "dcgfr56345.stage.lithium.com",
              "httpPort": 80,
              "httpsPort": 443,
              "originCertificate": "",
              "originCertsToHonor": "STANDARD_CERTIFICATE_AUTHORITIES",
              "originSni": true,
              "originType": "CUSTOMER",
              "ports": "",
              "standardCertificateAuthorities": [
                "akamai-permissive",
                "THIRD_PARTY_AMAZON"
              ],
              "trueClientIpClientSetting": false,
              "trueClientIpHeader": "True-Client-IP",
              "verificationMode": "CUSTOM",
              "minTlsVersion": "DYNAMIC",
              "ipVersion": "IPV4",
              "useUniqueCacheKey": false
            }
          },
          {
            "name": "modifyOutgoingResponseHeader",
            "options": {
              "action": "DELETE",
              "standardDeleteHeaderName": "OTHER",
              "customHeaderName": "X-Frame-Options"
            }
          },
          {
            "name": "modifyOutgoingResponseHeader",
            "options": {
              "action": "ADD",
              "standardAddHeaderName": "OTHER",
              "headerValue": "COMM_KH",
              "customHeaderName": "X-Org"
            }
          }
        ],
        "criteria": [
          {
            "name": "path",
            "options": {
              "matchOperator": "MATCHES_ONE_OF",
              "values": [
                "/community",
                "/community/*"
              ],
              "matchCaseSensitive": false,
              "normalize": false
            }
          },
          {
            "name": "path",
            "options": {
              "matchOperator": "DOES_NOT_MATCH_ONE_OF",
              "values": [
                "/community/sitemap*.xml"
              ],
              "matchCaseSensitive": false,
              "normalize": false
            }
          }
        ],
        "criteriaMustSatisfy": "all"
      },
      {
        "name": "App Fabric Origin",
        "children": [],
        "behaviors": [
          {
            "name": "origin",
            "options": {
              "originType": "CUSTOMER",
              "hostname": "s.example.com",
              "forwardHostHeader": "ORIGIN_HOSTNAME",
              "cacheKeyHostname": "ORIGIN_HOSTNAME",
              "compress": true,
              "enableTrueClientIp": true,
              "originCertificate": "",
              "verificationMode": "CUSTOM",
              "ports": "",
              "httpPort": 80,
              "httpsPort": 443,
              "trueClientIpHeader": "True-Client-IP",
              "trueClientIpClientSetting": false,
              "originSni": true,
              "customValidCnValues": [
                "{{Origin Hostname}}",
                "{{Forward Host Header}}"
              ],
              "originCertsToHonor": "STANDARD_CERTIFICATE_AUTHORITIES",
              "standardCertificateAuthorities": [
                "akamai-permissive"
              ],
              "minTlsVersion": "DYNAMIC",
              "ipVersion": "IPV4",
              "useUniqueCacheKey": false
            }
          },
          {
            "name": "modifyOutgoingRequestHeader",
            "options": {
              "action": "ADD",
              "standardAddHeaderName": "OTHER",
              "headerValue": "{{builtin.AK_HOST}}",
              "customHeaderName": "X-Forwarded-Host"
            }
          },
          {
            "name": "modifyOutgoingRequestHeader",
            "options": {
              "action": "DELETE",
              "standardDeleteHeaderName": "OTHER",
              "customHeaderName": "authorization"
            }
          },
          {
            "name": "modifyOutgoingResponseHeader",
            "options": {
              "action": "ADD",
              "standardAddHeaderName": "OTHER",
              "headerValue": "COMM-AF",
              "customHeaderName": "X-Org"
            }
          }
        ],
        "criteria": [
          {
            "name": "path",
            "options": {
              "matchOperator": "MATCHES_ONE_OF",
              "values": [
                "/example-support",
                "/example-support/en-us",
                "/example-support/en-us/*",
                "/example-support/",
                "/example-support/es-us",
                "/example-support/es-us/*"
              ],
              "matchCaseSensitive": false,
              "normalize": false
            }
          }
        ],
        "criteriaMustSatisfy": "all"
      },
      {
        "name": "PreRender Origin",
        "children": [],
        "behaviors": [
          {
            "name": "rewriteUrl",
            "options": {
              "behavior": "REWRITE",
              "targetUrl": "/render?url=https://{{builtin.AK_HOST}}{{builtin.AK_ORIGINAL_URL}}"
            }
          },
          {
            "name": "modifyOutgoingRequestHeader",
            "options": {
              "action": "DELETE",
              "standardDeleteHeaderName": "OTHER",
              "customHeaderName": "Cookie"
            }
          },
          {
            "name": "origin",
            "options": {
              "originType": "CUSTOMER",
              "hostname": "e.example.com",
              "forwardHostHeader": "REQUEST_HOST_HEADER",
              "cacheKeyHostname": "REQUEST_HOST_HEADER",
              "compress": true,
              "enableTrueClientIp": true,
              "originCertificate": "",
              "verificationMode": "CUSTOM",
              "ports": "",
              "httpPort": 80,
              "httpsPort": 443,
              "originSni": true,
              "customValidCnValues": [
                "{{Origin Hostname}}",
                "{{Forward Host Header}}"
              ],
              "originCertsToHonor": "STANDARD_CERTIFICATE_AUTHORITIES",
              "standardCertificateAuthorities": [
                "akamai-permissive",
                "THIRD_PARTY_AMAZON"
              ],
              "trueClientIpHeader": "True-Client-IP",
              "trueClientIpClientSetting": false,
              "minTlsVersion": "DYNAMIC",
              "ipVersion": "IPV4",
              "useUniqueCacheKey": false
            }
          },
          {
            "name": "modifyOutgoingResponseHeader",
            "options": {
              "action": "ADD",
              "standardAddHeaderName": "OTHER",
              "headerValue": "COMM-RENDERTRON",
              "customHeaderName": "X-Org"
            }
          }
        ],
        "criteria": [
          {
            "name": "fileExtension",
            "options": {
              "matchOperator": "IS_NOT_ONE_OF",
              "values": [
                "css",
                "js",
                "mp3",
                "txt",
                "zip",
                "jpg",
                "png",
                "avi",
                "doc",
                "wmv",
                "mov",
                "jpeg",
                "svg",
                "ico",
                "ttf",
                "woff",
                "woff2",
                "gif",
                "otf",
                "tff"
              ],
              "matchCaseSensitive": false
            }
          },
          {
            "name": "path",
            "options": {
              "matchOperator": "MATCHES_ONE_OF",
              "values": [
                "/community",
                "/community/*"
              ],
              "matchCaseSensitive": false,
              "normalize": false
            }
          },
          {
            "name": "regularExpression",
            "options": {
              "matchString": "{{user.PMUSER_USER_AGENT}}",
              "regex": "bot|crawl|archiver|transcoder|spider|uptime|validator|fetcher|cron|checker|reader|extractor|monitoring|analyzer|slurp|curl|bing|mediapartners",
              "caseSensitive": false
            }
          },
          {
            "name": "path",
            "options": {
              "matchOperator": "DOES_NOT_MATCH_ONE_OF",
              "values": [
                "/community/*/amp",
                "/community/sitemap*.xml",
                "/community/*/help/*/00/*",
                "/community/*/help/*/01/*"
              ],
              "matchCaseSensitive": false,
              "normalize": false
            }
          }
        ],
        "criteriaMustSatisfy": "all"
      },
      {
        "name": "PageSpeed Checks (Header)",
        "children": [],
        "behaviors": [
          {
            "name": "rewriteUrl",
            "options": {
              "behavior": "REWRITE",
              "targetUrl": "/render?url=https://{{builtin.AK_HOST}}{{builtin.AK_ORIGINAL_URL}}"
            }
          },
          {
            "name": "origin",
            "options": {
              "originType": "CUSTOMER",
              "hostname": "e.example.com",
              "forwardHostHeader": "REQUEST_HOST_HEADER",
              "cacheKeyHostname": "REQUEST_HOST_HEADER",
              "compress": true,
              "enableTrueClientIp": true,
              "originCertificate": "",
              "verificationMode": "CUSTOM",
              "ports": "",
              "httpPort": 80,
              "httpsPort": 443,
              "originSni": true,
              "trueClientIpHeader": "True-Client-IP",
              "trueClientIpClientSetting": false,
              "customValidCnValues": [
                "{{Origin Hostname}}",
                "{{Forward Host Header}}"
              ],
              "originCertsToHonor": "STANDARD_CERTIFICATE_AUTHORITIES",
              "standardCertificateAuthorities": [
                "akamai-permissive",
                "THIRD_PARTY_AMAZON"
              ],
              "minTlsVersion": "DYNAMIC",
              "ipVersion": "IPV4",
              "useUniqueCacheKey": false
            }
          },
          {
            "name": "caching",
            "options": {
              "behavior": "NO_STORE"
            }
          },
          {
            "name": "modifyOutgoingResponseHeader",
            "options": {
              "action": "ADD",
              "standardAddHeaderName": "OTHER",
              "headerValue": "COMM_PGH",
              "customHeaderName": "X-Org"
            }
          }
        ],
        "criteria": [
          {
            "name": "requestHeader",
            "options": {
              "headerName": "X-Pagespeed-Check",
              "matchOperator": "EXISTS",
              "matchWildcardName": false
            }
          }
        ],
        "criteriaMustSatisfy": "all",
        "comments": "Go to prerender endpoint whether its a bot or not (Backup test function)"
      },
      {
        "name": "PageSpeed Checks (QueryParam)",
        "children": [],
        "behaviors": [
          {
            "name": "rewriteUrl",
            "options": {
              "behavior": "REGEX_REPLACE",
              "matchRegex": "/(.*)(pagerender=true)(.*)",
              "targetRegex": "/render?url=https://{{builtin.AK_HOST}}/$1$3",
              "matchMultiple": true,
              "keepQueryString": true
            }
          },
          {
            "name": "origin",
            "options": {
              "originType": "CUSTOMER",
              "hostname": "e.example.com",
              "forwardHostHeader": "REQUEST_HOST_HEADER",
              "cacheKeyHostname": "REQUEST_HOST_HEADER",
              "compress": true,
              "enableTrueClientIp": true,
              "originCertificate": "",
              "verificationMode": "CUSTOM",
              "ports": "",
              "httpPort": 80,
              "httpsPort": 443,
              "originSni": true,
              "trueClientIpHeader": "True-Client-IP",
              "trueClientIpClientSetting": false,
              "customValidCnValues": [
                "{{Origin Hostname}}",
                "{{Forward Host Header}}"
              ],
              "originCertsToHonor": "STANDARD_CERTIFICATE_AUTHORITIES",
              "standardCertificateAuthorities": [
                "akamai-permissive",
                "THIRD_PARTY_AMAZON"
              ],
              "minTlsVersion": "DYNAMIC",
              "ipVersion": "IPV4",
              "useUniqueCacheKey": false
            }
          },
          {
            "name": "caching",
            "options": {
              "behavior": "NO_STORE"
            }
          },
          {
            "name": "modifyOutgoingRequestHeader",
            "options": {
              "action": "ADD",
              "standardAddHeaderName": "OTHER",
              "headerValue": "c.example.com",
              "customHeaderName": "X-Forwarded-Host"
            }
          },
          {
            "name": "modifyOutgoingRequestHeader",
            "options": {
              "action": "MODIFY",
              "standardModifyHeaderName": "USER_AGENT",
              "newHeaderValue": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
              "avoidDuplicateHeaders": false
            }
          },
          {
            "name": "modifyOutgoingResponseHeader",
            "options": {
              "action": "ADD",
              "standardAddHeaderName": "OTHER",
              "headerValue": "COMM_PGQ",
              "customHeaderName": "X-Org"
            }
          }
        ],
        "criteria": [
          {
            "name": "queryStringParameter",
            "options": {
              "parameterName": "pagerender",
              "matchOperator": "EXISTS",
              "matchWildcardName": false,
              "matchCaseSensitiveName": true
            }
          }
        ],
        "criteriaMustSatisfy": "all",
        "comments": "Go to prerender endpoint whether its a bot or not\nChecking and removing the queryparam so that the prerender (its a proxy!!) endpoint doesnt go into an infinite loop"
      }
    ],
    "behaviors": [
      {
        "name": "allHttpInCacheHierarchy",
        "options": {
          "enabled": true
        }
      },
      {
        "name": "setVariable",
        "options": {
          "variableName": "PMUSER_USER_AGENT",
          "valueSource": "EXTRACT",
          "transform": "NONE",
          "extractLocation": "CLIENT_REQUEST_HEADER",
          "headerName": "User-Agent"
        }
      },
      {
        "name": "edgeRedirector",
        "options": {
          "enabled": true,
          "cloudletPolicy": {
            "id": 116717,
            "name": "sgds_redirect_rules"
          },
          "isSharedPolicy": false
        }
      },
      {
        "name": "origin",
        "options": {
          "originType": "CUSTOMER",
          "hostname": "c.example.com",
          "forwardHostHeader": "REQUEST_HOST_HEADER",
          "cacheKeyHostname": "REQUEST_HOST_HEADER",
          "compress": true,
          "enableTrueClientIp": true,
          "originCertificate": "",
          "verificationMode": "CUSTOM",
          "ports": "",
          "httpPort": 80,
          "httpsPort": 443,
          "originSni": true,
          "customValidCnValues": [
            "{{Origin Hostname}}",
            "{{Forward Host Header}}",
            "s.example.com"
          ],
          "originCertsToHonor": "STANDARD_CERTIFICATE_AUTHORITIES",
          "standardCertificateAuthorities": [
            "akamai-permissive",
            "THIRD_PARTY_AMAZON"
          ],
          "trueClientIpHeader": "True-Client-IP",
          "trueClientIpClientSetting": false,
          "minTlsVersion": "DYNAMIC",
          "ipVersion": "IPV4",
          "tlsVersionTitle": "",
          "useUniqueCacheKey": false
        }
      },
      {
        "name": "cpCode",
        "options": {
          "value": {
            "id": 752101,
            "description": "s.example.com",
            "products": [
              "Fresca"
            ],
            "createdDate": 1537293470000,
            "cpCodeLimits": null,
            "name": "s.example.com"
          }
        }
      },
      {
        "name": "allowDelete",
        "options": {
          "enabled": true,
          "allowBody": true
        }
      },
      {
        "name": "allowPut",
        "options": {
          "enabled": true
        }
      },
      {
        "name": "report",
        "options": {
          "logHost": true,
          "logReferer": true,
          "logUserAgent": true,
          "logAcceptLanguage": false,
          "logCookies": "OFF",
          "logCustomLogField": false,
          "logEdgeIP": false,
          "logXForwardedFor": false
        }
      },
      {
        "name": "allowPost",
        "options": {
          "allowWithoutContentLength": false,
          "enabled": true
        }
      },
      {
        "name": "siteShield",
        "options": {
          "ssmap": {
            "name": "Ion Pre Prod (s2604.akamaiedge.net)",
            "value": "s2604.akamaiedge.net",
            "srmap": "example-Inc-e12443.akasrg.akamai.com",
            "hasMixedHosts": false,
            "src": "PREVIOUS_MAP"
          }
        }
      },
      {
        "name": "sureRoute",
        "options": {
          "enabled": true,
          "type": "CUSTOM_MAP",
          "testObjectUrl": "/500.html",
          "toHostStatus": "INCOMING_HH",
          "raceStatTtl": "30m",
          "forceSslForward": false,
          "enableCustomKey": false,
          "customMap": "example-Inc-e12443.akasrg.akamai.com",
          "srDownloadLinkTitle": ""
        }
      }
    ],
    "options": {
      "is_secure": true
    },
    "variables": [
      {
        "name": "PMUSER_COUNTRY",
        "value": "",
        "description": "",
        "hidden": true,
        "sensitive": false
      },
      {
        "name": "PMUSER_USER_AGENT",
        "value": "",
        "description": "",
        "hidden": false,
        "sensitive": false
      },
      {
        "name": "PMUSER_COOKIE_FILT",
        "value": "",
        "description": "",
        "hidden": true,
        "sensitive": false
      }
    ],
    "customOverride": {
      "overrideId": "cbo_465903994",
      "name": "embargo_geo_blocking "
    },
    "comments": "Redirects All traffic to a specific host"
  },
  "warnings": [
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/validation_message.ssl_custom_warning_test_staging",
      "errorLocation": "#/rules/behaviors/3",
      "detail": "If you are changing your `Origin Server` SSL Certificate Verification settings it is strongly recommended that you test on Staging before activating on Production. Failure to test on Staging may result in a service outage."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/validation_message.onlyonedge",
      "errorLocation": "#/rules/children/1/criteria/0",
      "detail": "The behaviors and matches enclosed within a `Client IP` match will only be executed by the Akamai edge server that receives the client request. If the request is forwarded to another Akamai server, the matches and behaviors enclosed will be ignored. If you are unsure about how this will affect your property please contact your Akamai Technical representative."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/validation_message.onlyonedge",
      "errorLocation": "#/rules/children/2/criteria/0",
      "detail": "The behaviors and matches enclosed within a `User Location Data` match will only be executed by the Akamai edge server that receives the client request. If the request is forwarded to another Akamai server, the matches and behaviors enclosed will be ignored. If you are unsure about how this will affect your property please contact your Akamai Technical representative."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/validation_message.onlyonedge",
      "errorLocation": "#/rules/children/2/criteria/1",
      "detail": "The behaviors and matches enclosed within a `User Location Data` match will only be executed by the Akamai edge server that receives the client request. If the request is forwarded to another Akamai server, the matches and behaviors enclosed will be ignored. If you are unsure about how this will affect your property please contact your Akamai Technical representative."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/incompatible_features",
      "errorLocation": "#/rules/children/5/behaviors/1",
      "detail": "`SetResponse Code` may not function as expected when used in conjunction with `Redirect`, because the status codes are not the same."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/validation_message.general_warning",
      "errorLocation": "#/rules/children/7/criteria/0",
      "detail": "Matching on `Request Type` requires thorough understanding of the way Akamai Edge servers process requests.  If you are unsure about how this will affect your property, please contact your Akamai Technical representative, and please test thoroughly on staging before activating on production."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/need_feature",
      "errorLocation": "#/rules/children/8/behaviors/0",
      "detail": "The Cache Key Query Parameters behavior should be set to ignore all when a NetStorage `Origin Server` is used. Netstorage does not honor query strings, so you should set this to avoid duplicate cache keys for the same object."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/need_feature",
      "errorLocation": "#/rules/children/8/behaviors/0",
      "detail": "When your `Origin Server` is set to NetStorage, enable Cache HTTP Error Responses with a TTL of at least 30 seconds."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/validation_message.ssl_custom_warning_test_staging",
      "errorLocation": "#/rules/children/9/behaviors/1",
      "detail": "If you are changing your `Origin Server` SSL Certificate Verification settings it is strongly recommended that you test on Staging before activating on Production. Failure to test on Staging may result in a service outage."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/validation_message.ssl_custom_warning_test_staging",
      "errorLocation": "#/rules/children/10/behaviors/1",
      "detail": "If you are changing your `Origin Server` SSL Certificate Verification settings it is strongly recommended that you test on Staging before activating on Production. Failure to test on Staging may result in a service outage."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/validation_message.ssl_custom_warning_test_staging",
      "errorLocation": "#/rules/children/11/behaviors/3",
      "detail": "If you are changing your `Origin Server` SSL Certificate Verification settings it is strongly recommended that you test on Staging before activating on Production. Failure to test on Staging may result in a service outage."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/validation_message.ssl_custom_warning_test_staging",
      "errorLocation": "#/rules/children/12/behaviors/0",
      "detail": "If you are changing your `Origin Server` SSL Certificate Verification settings it is strongly recommended that you test on Staging before activating on Production. Failure to test on Staging may result in a service outage."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/validation_message.general_warning",
      "errorLocation": "#/rules/children/13/criteria/2",
      "detail": "Matching on `Regex` can have a performance impact.  If you are unsure about how this will affectyour property, please contact your Akamai Technical representative, and please test thoroughly on staging before activating on production."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/cannot_validate",
      "errorLocation": "#/rules/children/13/behaviors/0/options/targetUrl",
      "detail": "The input to option Replace with of `Modify Outgoing Request Path` cannot be validated because of variable expression usage. Because of the use of variables, the value of the option is only known at runtime."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/validation_message.ssl_custom_warning_test_staging",
      "errorLocation": "#/rules/children/13/behaviors/2",
      "detail": "If you are changing your `Origin Server` SSL Certificate Verification settings it is strongly recommended that you test on Staging before activating on Production. Failure to test on Staging may result in a service outage."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/cannot_validate",
      "errorLocation": "#/rules/children/14/behaviors/0/options/targetUrl",
      "detail": "The input to option Replace with of `Modify Outgoing Request Path` cannot be validated because of variable expression usage. Because of the use of variables, the value of the option is only known at runtime."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/incompatible_condition",
      "errorLocation": "#/rules/children/14/behaviors/0",
      "detail": "Using the `Modify Outgoing Request Path` behavior within a match on `Request Header` will make it impossible to use the Content Control Utility to purge by URL. Please contact your Akamai Representative to explore alternative methods for making your content purgeable"
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/incompatible_condition",
      "errorLocation": "#/rules/children/14/behaviors/1",
      "detail": "Using the `Origin Server` behavior within a match on `Request Header` will make it impossible to use the Content Control Utility to purge by URL. Please contact your Akamai Representative to explorealternative methods for making your content purgeable"
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/validation_message.ssl_custom_warning_test_staging",
      "errorLocation": "#/rules/children/14/behaviors/1",
      "detail": "If you are changing your `Origin Server` SSL Certificate Verification settings it is strongly recommended that you test on Staging before activating on Production. Failure to test on Staging may result in a service outage."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/validation_message.warn_regex",
      "errorLocation": "#/rules/children/15/behaviors/0",
      "detail": "Format validation is not applied to the input fields when using the Regular Expression Replacement option in `Modify Outgoing Request Path`. Please test thoroughly on Akamai')s Staging Network when using this option. Do not hesitate to reach out to an Akamai Technical representative if you are uncertain about how this option is used."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/validation_message.ssl_custom_warning_test_staging",
      "errorLocation": "#/rules/children/15/behaviors/1",
      "detail": "If you are changing your `Origin Server` SSL Certificate Verification settings it is strongly recommended that you test on Staging before activating on Production. Failure to test on Staging may result in a service outage."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/advanced_override_metadata_enabled",
      "errorLocation": "#/rules",
      "detail": "This property contains <strong>advanced override metadata</strong>. This will potentially override any of the rule configurations that have been set above."
    },
    {
      "title": "Unstable rule format",
      "type": "https://problems.luna.akamaiapis.net/papi/v0/unstable_rule_format",
      "detail": "This property is using `latest` rule format, which is designed to reflect interface changes immediately. We suggest converting the property to a stable rule format such as `v2025-02-18` to minimize the risk of interface changes breaking your API client program.",
      "currentRuleFormat": "latest",
      "suggestedRuleFormat": "v2025-02-18"
    }
  ],
  "ruleFormat": "latest",
  "comments": "Rule format - custom override"
}
""",
    strict=False,
)

rule_tree_627844 = json.loads(
    """
{
  "accountId": "0-00AA",
  "contractId": "C-00AAA0A",
  "groupId": "12345",
  "propertyId": "627844",
  "propertyName": "p.example.ca",
  "propertyVersion": 108,
  "etag": "5d4250e3ddc06763cb46fe6cece881dc29cd5f39",
  "rules": {
    "name": "default",
    "children": [
      {
        "name": "Redirect to HTTPS",
        "children": [],
        "behaviors": [
          {
            "name": "redirect",
            "options": {
              "queryString": "APPEND",
              "responseCode": 301,
              "destinationHostname": "SAME_AS_REQUEST",
              "destinationPath": "SAME_AS_REQUEST",
              "destinationProtocol": "HTTPS",
              "mobileDefaultChoice": "DEFAULT"
            }
          }
        ],
        "criteria": [
          {
            "name": "requestProtocol",
            "options": {
              "value": "HTTP"
            }
          }
        ],
        "criteriaMustSatisfy": "all",
        "comments": "Redirect to the same URL on HTTPS protocol, issuing a 301 response code (Moved Permanently). You may change the response code to 302 if needed."
      },
      {
        "name": "CJ Site Integration",
        "children": [],
        "behaviors": [
          {
            "name": "origin",
            "options": {
              "originType": "CUSTOMER",
              "forwardHostHeader": "ORIGIN_HOSTNAME",
              "cacheKeyHostname": "ORIGIN_HOSTNAME",
              "compress": true,
              "enableTrueClientIp": true,
              "trueClientIpHeader": "X-Forwarded-For",
              "trueClientIpClientSetting": false,
              "verificationMode": "CUSTOM",
              "originSni": true,
              "httpPort": 80,
              "httpsPort": 443,
              "hostname": "www.mczbf.com",
              "originCertificate": "",
              "ports": "",
              "customValidCnValues": [
                "{{Origin Hostname}}"
              ],
              "originCertsToHonor": "STANDARD_CERTIFICATE_AUTHORITIES",
              "standardCertificateAuthorities": [
                "akamai-permissive"
              ],
              "minTlsVersion": "DYNAMIC",
              "ipVersion": "IPV4",
              "tlsVersionTitle": ""
            }
          },
          {
            "name": "caching",
            "options": {
              "behavior": "BYPASS_CACHE"
            }
          },
          {
            "name": "rewriteUrl",
            "options": {
              "behavior": "REMOVE",
              "matchMultiple": false,
              "keepQueryString": true,
              "match": "/proxydirectory/"
            }
          },
          {
            "name": "logCustom",
            "options": {
              "logCustomLogField": true,
              "customLogField": "{{builtin.AK_SCHEME}}"
            }
          },
          {
            "name": "modifyOutgoingRequestHeader",
            "options": {
              "action": "ADD",
              "standardAddHeaderName": "OTHER",
              "headerValue": "t.example.ca",
              "customHeaderName": "X-Forwarded-Host"
            }
          },
          {
            "name": "modifyOutgoingRequestHeader",
            "options": {
              "action": "ADD",
              "standardAddHeaderName": "OTHER",
              "headerValue": "t.example.ca",
              "customHeaderName": "X-Forwarded-Request-Host"
            }
          },
          {
            "name": "modifyOutgoingRequestHeader",
            "options": {
              "action": "ADD",
              "standardAddHeaderName": "OTHER",
              "headerValue": " /proxydirectory",
              "customHeaderName": "X-Forwarded-Request-Path"
            }
          },
          {
            "name": "modifyOutgoingRequestHeader",
            "options": {
              "action": "ADD",
              "standardAddHeaderName": "OTHER",
              "headerValue": "Example-Req-From-Akamai",
              "customHeaderName": "X-Forwarded-Server"
            }
          },
          {
            "name": "modifyOutgoingRequestHeader",
            "options": {
              "action": "ADD",
              "standardAddHeaderName": "OTHER",
              "headerValue": "t.example.ca",
              "customHeaderName": "Access-Control-Allow-Origin"
            }
          },
          {
            "name": "modifyOutgoingRequestHeader",
            "options": {
              "action": "ADD",
              "standardAddHeaderName": "OTHER",
              "headerValue": "s.example.ca",
              "customHeaderName": "Access-Control-Allow-Origin"
            }
          },
          {
            "name": "corsSupport",
            "options": {
              "enabled": true,
              "allowOrigins": "SPECIFIED",
              "allowCredentials": false,
              "allowHeaders": "ANY",
              "methods": [
                "GET",
                "POST"
              ],
              "preflightMaxAge": "600s",
              "exposeHeaders": [],
              "origins": [
                "t.example.ca",
                "s.example.ca"
              ]
            }
          },
          {
            "name": "setVariable",
            "options": {
              "valueSource": "EXPRESSION",
              "transform": "NONE",
              "variableName": "PMUSER_ORIGIN_NAME",
              "variableValue": "cj"
            }
          }
        ],
        "criteria": [
          {
            "name": "path",
            "options": {
              "matchOperator": "MATCHES_ONE_OF",
              "matchCaseSensitive": false,
              "values": [
                "/proxydirectory/*"
              ],
              "normalize": false
            }
          }
        ],
        "criteriaMustSatisfy": "all",
        "comments": ""
      },
      {
        "name": "Performance",
        "children": [
          {
            "name": "Compressible Objects",
            "children": [],
            "behaviors": [
              {
                "name": "gzipResponse",
                "options": {
                  "behavior": "ALWAYS"
                }
              }
            ],
            "criteria": [
              {
                "name": "contentType",
                "options": {
                  "matchCaseSensitive": false,
                  "matchOperator": "IS_ONE_OF",
                  "matchWildcard": true,
                  "values": [
                    "text/*",
                    "application/javascript",
                    "application/x-javascript",
                    "application/x-javascript*",
                    "application/json",
                    "application/x-json",
                    "application/*+json",
                    "application/*+xml",
                    "application/text",
                    "application/vnd.microsoft.icon",
                    "application/vnd-ms-fontobject",
                    "application/x-font-ttf",
                    "application/x-font-opentype",
                    "application/x-font-truetype",
                    "application/xmlfont/eot",
                    "application/xml",
                    "font/opentype",
                    "font/otf",
                    "font/eot",
                    "image/svg+xml",
                    "image/vnd.microsoft.icon"
                  ]
                }
              }
            ],
            "criteriaMustSatisfy": "all",
            "comments": "Compresses content to improve performance of clients with slow connections. Applies Last Mile Acceleration to requests when the returned object supports gzip compression."
          }
        ],
        "behaviors": [
          {
            "name": "enhancedAkamaiProtocol",
            "options": {
              "display": ""
            }
          },
          {
            "name": "http2",
            "options": {
              "enabled": ""
            }
          },
          {
            "name": "allowTransferEncoding",
            "options": {
              "enabled": true
            }
          },
          {
            "name": "removeVary",
            "options": {
              "enabled": true
            }
          },
          {
            "name": "sureRoute",
            "options": {
              "enabled": true,
              "forceSslForward": false,
              "raceStatTtl": "30m",
              "testObjectUrl": "/sureroute/sureroute-test-object.html",
              "toHostStatus": "INCOMING_HH",
              "type": "CUSTOM_MAP",
              "enableCustomKey": false,
              "srDownloadLinkTitle": "",
              "customMap": "Example-Inc-e3321.akasrg.akamai.com"
            }
          },
          {
            "name": "prefetch",
            "options": {
              "enabled": true
            }
          }
        ],
        "criteria": [],
        "criteriaMustSatisfy": "all",
        "comments": "Improves the performance of delivering objects to end users. Behaviors in this rule are applied to all requests as appropriate."
      },
      {
        "name": "Offload",
        "children": [
          {
            "name": "Flat File From Netstorage",
            "children": [],
            "behaviors": [
              {
                "name": "setVariable",
                "options": {
                  "valueSource": "EXPRESSION",
                  "transform": "SUBSTITUTE",
                  "variableName": "PMUSER_FILENAME",
                  "variableValue": " {{builtin.AK_FILENAME}}",
                  "regex": "^(.*)(.)(.*)$",
                  "replacement": "$1",
                  "caseSensitive": true,
                  "globalSubstitution": false
                }
              },
              {
                "name": "failAction",
                "options": {
                  "enabled": true,
                  "actionType": "RECREATED_NS",
                  "netStorageHostname": {
                    "cpCode": 590357,
                    "downloadDomainName": "examplegpm.download.akamai.com",
                    "g2oToken": null
                  },
                  "netStoragePath": "/flatfiles{{builtin.AK_BASE_URL}}/{{user.PMUSER_FILENAME}}.html",
                  "cpCode": {
                    "id": 1056780,
                    "description": "t.example.ca",
                    "products": [
                      "Fresca"
                    ],
                    "createdDate": 1591805961000,
                    "cpCodeLimits": null,
                    "name": "t.example.ca"
                  },
                  "statusCode": 200
                }
              }
            ],
            "criteria": [
              {
                "name": "path",
                "options": {
                  "matchOperator": "MATCHES_ONE_OF",
                  "values": [
                    "/ressources-impot/impot-medical-et-handicap/*",
                    "/ressources-impot/impot-evenements-de-la-vie/*",
                    "/ressources-impot/impot-revenus/*",
                    "/ressources-impot/impot-proprietaire-foncier/*",
                    "/ressources-impot/impot-etudiants/*",
                    "/ressources-impot/impot-programmes-federaux/*",
                    "/ressources-impot/impot-economies/*",
                    "/ressources-impot/impot-mariage/*",
                    "/ressources-impot/impot-personnes-a-charge/*",
                    "/ressources-impot/impot-securite/*",
                    "/ressources-impot/impot-retraite/*",
                    "/ressources-impot/impot-deductions/*",
                    "/ressources-impot/impot-production-declarations/*",
                    "/ressources-impot/impot-gratuit/*",
                    "/ressources-impot/formulaire-t1036.jsp",
                    "/ressources-impot/impot-revenu-imposable/*",
                    "/ressources-impot/impot-arc/*",
                    "/ressources-impot/impot-proprietaire-entreprise/*",
                    "/ressources-impot/impot-placements/*",
                    "/ressources-impot/impot-revenu-etranger/*",
                    "/ressources-impot/impot-conformite/*",
                    "/logiciels-impot/revision-pro-condition.jsp",
                    "/logiciel/revision-pro/conditions-modal-content.jsp",
                    "/logiciel/revision-pro/conditions.jsp",
                    "/logiciel/iro/disponible-bientot.jsp",
                    "/logiciel/iro/open.jsp",
                    "/logiciel/cfd/conditions.jsp"
                  ],
                  "matchCaseSensitive": false,
                  "normalize": false
                }
              },
              {
                "name": "fileExtension",
                "options": {
                  "matchOperator": "IS_ONE_OF",
                  "matchCaseSensitive": false,
                  "values": [
                    "jsp"
                  ]
                }
              }
            ],
            "criteriaMustSatisfy": "all",
            "comments": ""
          },
          {
            "name": "Static Objects Blog",
            "children": [],
            "behaviors": [
              {
                "name": "caching",
                "options": {
                  "behavior": "MAX_AGE",
                  "mustRevalidate": false,
                  "ttl": "365d"
                }
              },
              {
                "name": "prefreshCache",
                "options": {
                  "enabled": true,
                  "prefreshval": 90
                }
              }
            ],
            "criteria": [
              {
                "name": "fileExtension",
                "options": {
                  "matchCaseSensitive": false,
                  "matchOperator": "IS_ONE_OF",
                  "values": [
                    "aif",
                    "aiff",
                    "au",
                    "avi",
                    "bin",
                    "bmp",
                    "cab",
                    "carb",
                    "cct",
                    "cdf",
                    "class",
                    "doc",
                    "dcr",
                    "dtd",
                    "exe",
                    "flv",
                    "gcf",
                    "gff",
                    "gif",
                    "grv",
                    "hdml",
                    "hqx",
                    "ico",
                    "ini",
                    "jpeg",
                    "jpg",
                    "mov",
                    "mp3",
                    "nc",
                    "pct",
                    "pdf",
                    "png",
                    "ppc",
                    "pws",
                    "swa",
                    "swf",
                    "txt",
                    "vbs",
                    "w32",
                    "wav",
                    "wbmp",
                    "wml",
                    "wmlc",
                    "wmls",
                    "wmlsc",
                    "xsd",
                    "zip",
                    "pict",
                    "tif",
                    "tiff",
                    "mid",
                    "midi",
                    "ttf",
                    "eot",
                    "woff",
                    "woff2",
                    "otf",
                    "svg",
                    "svgz",
                    "webp",
                    "jxr",
                    "jar",
                    "jp2"
                  ]
                }
              },
              {
                "name": "path",
                "options": {
                  "matchOperator": "MATCHES_ONE_OF",
                  "values": [
                    "/info*",
                    "/tips*"
                  ],
                  "matchCaseSensitive": false,
                  "normalize": false
                }
              }
            ],
            "criteriaMustSatisfy": "any",
            "comments": "Overrides the default caching behavior for images, music, and similar objects that are cached on the edge server. Because these object types are static, the TTL is long."
          },
          {
            "name": "Blog Caching",
            "children": [],
            "behaviors": [
              {
                "name": "caching",
                "options": {
                  "behavior": "MAX_AGE",
                  "mustRevalidate": false,
                  "ttl": "30s"
                }
              },
              {
                "name": "prefreshCache",
                "options": {
                  "enabled": true,
                  "prefreshval": 90
                }
              }
            ],
            "criteria": [
              {
                "name": "path",
                "options": {
                  "matchOperator": "MATCHES_ONE_OF",
                  "values": [
                    "/info*",
                    "/tips*"
                  ],
                  "matchCaseSensitive": false,
                  "normalize": false
                }
              }
            ],
            "criteriaMustSatisfy": "any",
            "comments": "Overrides the default caching behavior for images, music, and similar objects that are cached on the edge server. Because these object types are static, the TTL is long."
          },
          {
            "name": "CSS and JavaScript",
            "children": [],
            "behaviors": [
              {
                "name": "caching",
                "options": {
                  "behavior": "MAX_AGE",
                  "mustRevalidate": false,
                  "ttl": "1d"
                }
              },
              {
                "name": "prefreshCache",
                "options": {
                  "enabled": true,
                  "prefreshval": 90
                }
              },
              {
                "name": "prefetchable",
                "options": {
                  "enabled": true
                }
              }
            ],
            "criteria": [
              {
                "name": "fileExtension",
                "options": {
                  "matchCaseSensitive": false,
                  "matchOperator": "IS_ONE_OF",
                  "values": [
                    "css",
                    "js"
                  ]
                }
              }
            ],
            "criteriaMustSatisfy": "any",
            "comments": "Overrides the default caching behavior for CSS and JavaScript objects that are cached on the edge server. Because these object types are dynamic, the TTL is brief."
          },
          {
            "name": "Static Objects",
            "children": [],
            "behaviors": [
              {
                "name": "caching",
                "options": {
                  "behavior": "MAX_AGE",
                  "mustRevalidate": false,
                  "ttl": "7d"
                }
              },
              {
                "name": "prefreshCache",
                "options": {
                  "enabled": true,
                  "prefreshval": 90
                }
              },
              {
                "name": "prefetchable",
                "options": {
                  "enabled": true
                }
              }
            ],
            "criteria": [
              {
                "name": "fileExtension",
                "options": {
                  "matchCaseSensitive": false,
                  "matchOperator": "IS_ONE_OF",
                  "values": [
                    "aif",
                    "aiff",
                    "au",
                    "avi",
                    "bin",
                    "bmp",
                    "cab",
                    "carb",
                    "cct",
                    "cdf",
                    "class",
                    "doc",
                    "dcr",
                    "dtd",
                    "exe",
                    "flv",
                    "gcf",
                    "gff",
                    "gif",
                    "grv",
                    "hdml",
                    "hqx",
                    "ico",
                    "ini",
                    "jpeg",
                    "jpg",
                    "mov",
                    "mp3",
                    "nc",
                    "pct",
                    "pdf",
                    "png",
                    "ppc",
                    "pws",
                    "swa",
                    "swf",
                    "txt",
                    "vbs",
                    "w32",
                    "wav",
                    "wbmp",
                    "wml",
                    "wmlc",
                    "wmls",
                    "wmlsc",
                    "xsd",
                    "zip",
                    "pict",
                    "tif",
                    "tiff",
                    "mid",
                    "midi",
                    "ttf",
                    "eot",
                    "woff",
                    "woff2",
                    "otf",
                    "svg",
                    "svgz",
                    "webp",
                    "jxr",
                    "jar",
                    "jp2"
                  ]
                }
              }
            ],
            "criteriaMustSatisfy": "any",
            "comments": "Overrides the default caching behavior for images, music, and similar objects that are cached on the edge server. Because these object types are static, the TTL is long."
          },
          {
            "name": "Uncacheable Responses",
            "children": [],
            "behaviors": [
              {
                "name": "downstreamCache",
                "options": {
                  "behavior": "TUNNEL_ORIGIN"
                }
              }
            ],
            "criteria": [
              {
                "name": "cacheability",
                "options": {
                  "matchOperator": "IS_NOT",
                  "value": "CACHEABLE"
                }
              }
            ],
            "criteriaMustSatisfy": "all",
            "comments": "Overrides the default downstream caching behavior for uncacheable object types. Instructs the edge server to pass Cache-Control and/or Expire headers from the origin to the client."
          }
        ],
        "behaviors": [
          {
            "name": "caching",
            "options": {
              "behavior": "NO_STORE"
            }
          },
          {
            "name": "cacheError",
            "options": {
              "enabled": true,
              "preserveStale": true,
              "ttl": "10s"
            }
          },
          {
            "name": "downstreamCache",
            "options": {
              "allowBehavior": "LESSER",
              "behavior": "ALLOW",
              "sendHeaders": "CACHE_CONTROL_AND_EXPIRES",
              "sendPrivate": false
            }
          }
        ],
        "criteria": [],
        "criteriaMustSatisfy": "all",
        "comments": "Controls caching, which offloads traffic away from the origin. Most objects types are not cached. However, the child rules override this behavior for certain subsets of requests."
      },
      {
        "name": "Deny ldap",
        "children": [],
        "behaviors": [
          {
            "name": "denyAccess",
            "options": {
              "reason": "default-deny-reason",
              "enabled": true
            }
          }
        ],
        "criteria": [
          {
            "name": "userAgent",
            "options": {
              "matchOperator": "IS_ONE_OF",
              "values": [
                "*jndi:*"
              ],
              "matchWildcard": true,
              "matchCaseSensitive": false
            }
          }
        ],
        "criteriaMustSatisfy": "all"
      },
      {
        "name": "Redirect Top Level",
        "children": [],
        "behaviors": [
          {
            "name": "redirect",
            "options": {
              "queryString": "APPEND",
              "responseCode": 301,
              "destinationHostname": "OTHER",
              "destinationPath": "SAME_AS_REQUEST",
              "destinationProtocol": "SAME_AS_REQUEST",
              "mobileDefaultChoice": "DEFAULT",
              "destinationHostnameOther": "t.example.ca"
            }
          }
        ],
        "criteria": [
          {
            "name": "hostname",
            "options": {
              "matchOperator": "IS_ONE_OF",
              "values": [
                "w.example.ca"
              ]
            }
          }
        ],
        "criteriaMustSatisfy": "all",
        "comments": ""
      },
      {
        "name": "Netstorage t.example.ca folder",
        "children": [
          {
            "name": "Netstorage t.example.ca folder",
            "children": [],
            "behaviors": [
              {
                "name": "rewriteUrl",
                "options": {
                  "behavior": "PREPEND",
                  "targetPathPrepend": "/t.example.ca/",
                  "keepQueryString": false
                }
              }
            ],
            "criteria": [
              {
                "name": "path",
                "options": {
                  "matchOperator": "MATCHES_ONE_OF",
                  "values": [
                    "/sitemap.xml"
                  ],
                  "matchCaseSensitive": false,
                  "normalize": false
                }
              }
            ],
            "criteriaMustSatisfy": "all",
            "comments": ""
          }
        ],
        "behaviors": [
          {
            "name": "origin",
            "options": {
              "originType": "NET_STORAGE",
              "netStorage": {
                "downloadDomainName": "examplegpm.download.akamai.com",
                "cpCode": 590357,
                "g2oToken": null
              }
            }
          },
          {
            "name": "caching",
            "options": {
              "behavior": "MAX_AGE",
              "mustRevalidate": false,
              "ttl": "10m"
            }
          },
          {
            "name": "cacheKeyQueryParams",
            "options": {
              "behavior": "IGNORE_ALL"
            }
          },
          {
            "name": "cacheError",
            "options": {
              "enabled": true,
              "ttl": "31s",
              "preserveStale": true
            }
          },
          {
            "name": "rewriteUrl",
            "options": {
              "behavior": "PREPEND",
              "targetPathPrepend": "/t.example.ca/",
              "keepQueryString": false
            }
          },
          {
            "name": "setVariable",
            "options": {
              "valueSource": "EXPRESSION",
              "transform": "NONE",
              "variableName": "PMUSER_ORIGIN_NAME",
              "variableValue": "netstorage"
            }
          }
        ],
        "criteria": [
          {
            "name": "path",
            "options": {
              "matchOperator": "MATCHES_ONE_OF",
              "values": [
                "/robots.txt",
                "/googlef2feb1480d7429b5.html",
                "/sitemap.xml"
              ],
              "matchCaseSensitive": false,
              "normalize": false
            }
          }
        ],
        "criteriaMustSatisfy": "all",
        "comments": ""
      },
      {
        "name": "Netstorage GWP Static Files",
        "children": [],
        "behaviors": [
          {
            "name": "origin",
            "options": {
              "originType": "NET_STORAGE",
              "netStorage": {
                "cpCode": 273118,
                "downloadDomainName": "example.download.akamai.com",
                "g2oToken": null
              }
            }
          },
          {
            "name": "caching",
            "options": {
              "behavior": "MAX_AGE",
              "mustRevalidate": false,
              "ttl": "10d"
            }
          },
          {
            "name": "rewriteUrl",
            "options": {
              "behavior": "PREPEND",
              "keepQueryString": false,
              "targetPathPrepend": "/prod/"
            }
          },
          {
            "name": "setVariable",
            "options": {
              "valueSource": "EXPRESSION",
              "transform": "NONE",
              "variableName": "PMUSER_ORIGIN_NAME",
              "variableValue": "netstorage"
            }
          }
        ],
        "criteria": [
          {
            "name": "hostname",
            "options": {
              "matchOperator": "IS_ONE_OF",
              "values": [
                "t.example.ca"
              ]
            }
          },
          {
            "name": "path",
            "options": {
              "matchOperator": "MATCHES_ONE_OF",
              "matchCaseSensitive": false,
              "normalize": false,
              "values": [
                "/file/*"
              ]
            }
          }
        ],
        "criteriaMustSatisfy": "all",
        "comments": ""
      },
      {
        "name": "TICa Download Pages Caching",
        "children": [],
        "behaviors": [
          {
            "name": "caching",
            "options": {
              "behavior": "MAX_AGE",
              "mustRevalidate": false,
              "ttl": "1h"
            }
          },
          {
            "name": "cacheKeyQueryParams",
            "options": {
              "behavior": "IGNORE_ALL"
            }
          }
        ],
        "criteria": [
          {
            "name": "path",
            "options": {
              "matchOperator": "MATCHES_ONE_OF",
              "matchCaseSensitive": false,
              "normalize": false,
              "values": [
                "/impot/logiciels/installation"
              ]
            }
          }
        ],
        "criteriaMustSatisfy": "all",
        "comments": ""
      },
      {
        "name": "DenyActuatorUris",
        "children": [],
        "behaviors": [
          {
            "name": "denyAccess",
            "options": {
              "reason": "default-deny-reason",
              "enabled": true
            }
          }
        ],
        "criteria": [
          {
            "name": "path",
            "options": {
              "matchOperator": "MATCHES_ONE_OF",
              "values": [
                "/manage*"
              ],
              "matchCaseSensitive": false,
              "normalize": false
            }
          }
        ],
        "criteriaMustSatisfy": "all",
        "comments": ""
      },
      {
        "name": "mPulse",
        "children": [],
        "behaviors": [
          {
            "name": "mPulse",
            "options": {
              "enabled": true,
              "requirePci": false,
              "loaderVersion": "V12",
              "configOverride": "",
              "titleOptional": "",
              "apiKey": "4YVNW-5BSD9-66W8V-J58LH-6YL7D",
              "bufferSize": ""
            }
          }
        ],
        "criteria": [],
        "criteriaMustSatisfy": "all",
        "comments": ""
      },
      {
        "name": "Priority Code rules",
        "children": [
          {
            "name": "Remove PnP pCode",
            "children": [],
            "behaviors": [
              {
                "name": "removeQueryParameter",
                "options": {
                  "parameters": [
                    "priorityCode"
                  ]
                }
              }
            ],
            "criteria": [
              {
                "name": "path",
                "options": {
                  "matchOperator": "MATCHES_ONE_OF",
                  "matchCaseSensitive": false,
                  "normalize": false,
                  "values": [
                    "/impot/prix"
                  ]
                }
              }
            ],
            "criteriaMustSatisfy": "all",
            "comments": ""
          },
          {
            "name": "Set Variable: PRIORITY_CODE",
            "children": [],
            "behaviors": [
              {
                "name": "setVariable",
                "options": {
                  "valueSource": "EXTRACT",
                  "transform": "NONE",
                  "variableName": "PMUSER_PRIORITY_CODE",
                  "extractLocation": "QUERY_STRING",
                  "queryParameterName": "priorityCode"
                }
              }
            ],
            "criteria": [
              {
                "name": "queryStringParameter",
                "options": {
                  "matchOperator": "EXISTS",
                  "matchWildcardName": false,
                  "matchCaseSensitiveName": true,
                  "parameterName": "priorityCode"
                }
              }
            ],
            "criteriaMustSatisfy": "all",
            "comments": ""
          },
          {
            "name": "Set Cookie: priorityCode",
            "children": [],
            "behaviors": [
              {
                "name": "responseCookie",
                "options": {
                  "enabled": true,
                  "type": "FIXED",
                  "defaultDomain": false,
                  "defaultPath": false,
                  "expires": "ON_BROWSER_CLOSE",
                  "sameSite": "DEFAULT",
                  "secure": true,
                  "httpOnly": false,
                  "cookieName": "priorityCode",
                  "value": "{{user.PMUSER_PRIORITY_CODE}}",
                  "domain": "example.ca",
                  "path": "/"
                }
              }
            ],
            "criteria": [
              {
                "name": "queryStringParameter",
                "options": {
                  "matchOperator": "EXISTS",
                  "matchWildcardName": false,
                  "matchCaseSensitiveName": true,
                  "parameterName": "priorityCode"
                }
              },
              {
                "name": "path",
                "options": {
                  "matchOperator": "MATCHES_ONE_OF",
                  "matchCaseSensitive": false,
                  "normalize": false,
                  "values": [
                    "/affilie/*",
                    "/partenaire/*",
                    "/offres/*",
                    "/se/*"
                  ]
                }
              }
            ],
            "criteriaMustSatisfy": "all",
            "comments": ""
          },
          {
            "name": "Set Cookie: _pcode",
            "children": [],
            "behaviors": [
              {
                "name": "responseCookie",
                "options": {
                  "enabled": true,
                  "type": "FIXED",
                  "defaultDomain": false,
                  "defaultPath": false,
                  "expires": "ON_BROWSER_CLOSE",
                  "sameSite": "DEFAULT",
                  "secure": true,
                  "httpOnly": false,
                  "cookieName": "_pcode",
                  "value": "{{user.PMUSER_PRIORITY_CODE}}",
                  "domain": "example.ca",
                  "path": "/"
                }
              }
            ],
            "criteria": [
              {
                "name": "queryStringParameter",
                "options": {
                  "matchOperator": "EXISTS",
                  "matchWildcardName": false,
                  "matchCaseSensitiveName": true,
                  "parameterName": "priorityCode"
                }
              },
              {
                "name": "path",
                "options": {
                  "matchOperator": "MATCHES_ONE_OF",
                  "matchCaseSensitive": false,
                  "normalize": false,
                  "values": [
                    "/affilie/*",
                    "/partenaire/*",
                    "/offres/*",
                    "/se/*"
                  ]
                }
              }
            ],
            "criteriaMustSatisfy": "all",
            "comments": ""
          }
        ],
        "behaviors": [],
        "criteria": [],
        "criteriaMustSatisfy": "all",
        "comments": ""
      },
      {
        "name": "Prod GWP Rendering Service Origin",
        "children": [],
        "behaviors": [
          {
            "name": "origin",
            "options": {
              "originType": "CUSTOMER",
              "forwardHostHeader": "ORIGIN_HOSTNAME",
              "cacheKeyHostname": "REQUEST_HOST_HEADER",
              "ipVersion": "IPV4",
              "compress": true,
              "enableTrueClientIp": true,
              "trueClientIpHeader": "True-Client-IP",
              "trueClientIpClientSetting": false,
              "verificationMode": "CUSTOM",
              "originSni": true,
              "httpPort": 80,
              "httpsPort": 443,
              "minTlsVersion": "DYNAMIC",
              "hostname": "r.example.com",
              "originCertificate": "",
              "ports": "",
              "tlsVersionTitle": "",
              "customValidCnValues": [
                "{{Origin Hostname}}",
                "{{Forward Host Header}}"
              ],
              "originCertsToHonor": "STANDARD_CERTIFICATE_AUTHORITIES",
              "standardCertificateAuthorities": [
                "akamai-permissive"
              ]
            }
          },
          {
            "name": "setVariable",
            "options": {
              "valueSource": "EXPRESSION",
              "transform": "NONE",
              "variableName": "PMUSER_ORIGIN_NAME",
              "variableValue": "raas"
            }
          }
        ],
        "criteria": [
          {
            "name": "hostname",
            "options": {
              "matchOperator": "IS_ONE_OF",
              "values": [
                "t.example.ca"
              ]
            }
          },
          {
            "name": "path",
            "options": {
              "matchOperator": "MATCHES_ONE_OF",
              "matchCaseSensitive": false,
              "normalize": false,
              "values": [
                "/_next/*",
                "/gwp-components/*",
                "/gwp-cg-components/*"
              ]
            }
          }
        ],
        "criteriaMustSatisfy": "all",
        "comments": ""
      },
      {
        "name": "Blog failover",
        "children": [],
        "behaviors": [
          {
            "name": "failAction",
            "options": {
              "enabled": true,
              "actionType": "REDIRECT",
              "redirectHostnameType": "ORIGINAL",
              "redirectCustomPath": true,
              "redirectMethod": 301,
              "preserveQueryString": false,
              "modifyProtocol": false,
              "redirectPath": "/info/"
            }
          }
        ],
        "criteria": [
          {
            "name": "path",
            "options": {
              "matchOperator": "MATCHES_ONE_OF",
              "matchCaseSensitive": false,
              "normalize": false,
              "values": [
                "/info*",
                "/tips*"
              ]
            }
          },
          {
            "name": "matchResponseCode",
            "options": {
              "matchOperator": "IS_ONE_OF",
              "values": [
                "404"
              ]
            }
          }
        ],
        "criteriaMustSatisfy": "all"
      },
      {
        "name": " Tag conditional origin",
        "children": [],
        "behaviors": [
          {
            "name": "setVariable",
            "options": {
              "valueSource": "EXPRESSION",
              "transform": "NONE",
              "variableName": "PMUSER_ORIGIN_NAME",
              "variableValue": "conditional"
            }
          }
        ],
        "criteria": [
          {
            "name": "path",
            "options": {
              "matchOperator": "MATCHES_ONE_OF",
              "matchCaseSensitive": false,
              "normalize": false,
              "values": [
                "/v1/graphql"
              ]
            }
          }
        ],
        "criteriaMustSatisfy": "all",
        "comments": ""
      },
      {
        "name": "GWP Web Orchestrator Origin",
        "children": [
          {
            "name": "Prod GWP Origin",
            "children": [
              {
                "name": "Apply Cloudlet Security",
                "children": [],
                "behaviors": [
                  {
                    "name": "requestControl",
                    "options": {
                      "enabled": true,
                      "isSharedPolicy": false,
                      "enableBranded403": false,
                      "cloudletPolicy": {
                        "id": 47702,
                        "name": "Example_IP_AND_TEP_INGRESS"
                      }
                    }
                  }
                ],
                "criteria": [
                  {
                    "name": "requestType",
                    "options": {
                      "matchOperator": "IS_NOT",
                      "value": "EW_SUBREQUEST"
                    }
                  },
                  {
                    "name": "path",
                    "options": {
                      "matchOperator": "MATCHES_ONE_OF",
                      "matchCaseSensitive": false,
                      "normalize": false,
                      "values": [
                        "/gwp/*"
                      ]
                    }
                  }
                ],
                "criteriaMustSatisfy": "all",
                "comments": ""
              }
            ],
            "behaviors": [],
            "criteria": [
              {
                "name": "requestHeader",
                "options": {
                  "matchOperator": "DOES_NOT_EXIST",
                  "matchWildcardName": false,
                  "headerName": "target-env"
                }
              }
            ],
            "criteriaMustSatisfy": "all",
            "comments": "Load Balanced WebOrchestrator API Gateway Origin (API GW Decides Blue vs Green Percentage here)"
          },
          {
            "name": "Prod GWP Origin (Blue)",
            "children": [
              {
                "name": "Apply Cloudlet Security",
                "children": [],
                "behaviors": [
                  {
                    "name": "requestControl",
                    "options": {
                      "enabled": true,
                      "isSharedPolicy": false,
                      "enableBranded403": false,
                      "cloudletPolicy": {
                        "id": 47702,
                        "name": "Example_IP_AND_TEP_INGRESS"
                      }
                    }
                  }
                ],
                "criteria": [
                  {
                    "name": "requestType",
                    "options": {
                      "matchOperator": "IS_NOT",
                      "value": "EW_SUBREQUEST"
                    }
                  }
                ],
                "criteriaMustSatisfy": "all",
                "comments": ""
              }
            ],
            "behaviors": [
              {
                "name": "origin",
                "options": {
                  "originType": "CUSTOMER",
                  "forwardHostHeader": "ORIGIN_HOSTNAME",
                  "cacheKeyHostname": "REQUEST_HOST_HEADER",
                  "ipVersion": "IPV4",
                  "compress": true,
                  "enableTrueClientIp": true,
                  "trueClientIpHeader": "True-Client-IP",
                  "trueClientIpClientSetting": false,
                  "verificationMode": "CUSTOM",
                  "originSni": true,
                  "httpPort": 80,
                  "httpsPort": 443,
                  "minTlsVersion": "DYNAMIC",
                  "hostname": "w.example.com",
                  "originCertificate": "",
                  "ports": "",
                  "tlsVersionTitle": "",
                  "customValidCnValues": [
                    "{{Origin Hostname}}",
                    "{{Forward Host Header}}"
                  ],
                  "originCertsToHonor": "STANDARD_CERTIFICATE_AUTHORITIES",
                  "standardCertificateAuthorities": [
                    "akamai-permissive"
                  ]
                }
              }
            ],
            "criteria": [
              {
                "name": "requestHeader",
                "options": {
                  "matchOperator": "EXISTS",
                  "matchWildcardName": false,
                  "headerName": "target-env"
                }
              },
              {
                "name": "requestHeader",
                "options": {
                  "matchOperator": "IS_ONE_OF",
                  "matchWildcardName": false,
                  "matchWildcardValue": false,
                  "matchCaseSensitiveValue": true,
                  "headerName": "target-env",
                  "values": [
                    "blue",
                    "BLUE",
                    "Blue"
                  ]
                }
              }
            ],
            "criteriaMustSatisfy": "all",
            "comments": "Web Orchestrator API Gateway Origin - Target Blue env directly (Allowed within Example VPN only)"
          },
          {
            "name": "Prod GWP Origin (Green)",
            "children": [
              {
                "name": "Apply Cloudlet Security",
                "children": [],
                "behaviors": [
                  {
                    "name": "requestControl",
                    "options": {
                      "enabled": true,
                      "isSharedPolicy": false,
                      "enableBranded403": false,
                      "cloudletPolicy": {
                        "id": 47702,
                        "name": "Example_IP_AND_TEP_INGRESS"
                      }
                    }
                  }
                ],
                "criteria": [
                  {
                    "name": "requestType",
                    "options": {
                      "matchOperator": "IS_NOT",
                      "value": "EW_SUBREQUEST"
                    }
                  }
                ],
                "criteriaMustSatisfy": "all",
                "comments": ""
              }
            ],
            "behaviors": [
              {
                "name": "origin",
                "options": {
                  "originType": "CUSTOMER",
                  "forwardHostHeader": "ORIGIN_HOSTNAME",
                  "cacheKeyHostname": "REQUEST_HOST_HEADER",
                  "ipVersion": "IPV4",
                  "compress": true,
                  "enableTrueClientIp": true,
                  "trueClientIpHeader": "True-Client-IP",
                  "trueClientIpClientSetting": false,
                  "verificationMode": "CUSTOM",
                  "originSni": true,
                  "httpPort": 80,
                  "httpsPort": 443,
                  "minTlsVersion": "DYNAMIC",
                  "hostname": "w.example.com",
                  "originCertificate": "",
                  "ports": "",
                  "tlsVersionTitle": "",
                  "customValidCnValues": [
                    "{{Origin Hostname}}",
                    "{{Forward Host Header}}"
                  ],
                  "originCertsToHonor": "STANDARD_CERTIFICATE_AUTHORITIES",
                  "standardCertificateAuthorities": [
                    "akamai-permissive"
                  ]
                }
              }
            ],
            "criteria": [
              {
                "name": "requestHeader",
                "options": {
                  "matchOperator": "EXISTS",
                  "matchWildcardName": false,
                  "headerName": "target-env"
                }
              },
              {
                "name": "requestHeader",
                "options": {
                  "matchOperator": "IS_ONE_OF",
                  "matchWildcardName": false,
                  "matchWildcardValue": false,
                  "matchCaseSensitiveValue": true,
                  "headerName": "target-env",
                  "values": [
                    "green",
                    "GREEN",
                    "Green"
                  ]
                }
              }
            ],
            "criteriaMustSatisfy": "all",
            "comments": "Web Orchestrator API Gateway Origin - Target Green env directly (Allowed within Example VPN only)"
          },
          {
            "name": "Prepend /public/",
            "children": [],
            "behaviors": [
              {
                "name": "rewriteUrl",
                "options": {
                  "behavior": "PREPEND",
                  "keepQueryString": true,
                  "targetPathPrepend": "/public/"
                }
              }
            ],
            "criteria": [
              {
                "name": "path",
                "options": {
                  "matchOperator": "DOES_NOT_MATCH_ONE_OF",
                  "matchCaseSensitive": false,
                  "normalize": false,
                  "values": [
                    "*/amp/*",
                    "/hashes/*",
                    "/amp/link/*",
                    "/pages/*"
                  ]
                }
              }
            ],
            "criteriaMustSatisfy": "all",
            "comments": ""
          },
          {
            "name": "S3 Fallback /pages/* Append page.html",
            "children": [],
            "behaviors": [
              {
                "name": "rewriteUrl",
                "options": {
                  "behavior": "REWRITE",
                  "targetUrl": "{{builtin.AK_PATH}}/page.html"
                }
              }
            ],
            "criteria": [
              {
                "name": "path",
                "options": {
                  "matchOperator": "MATCHES_ONE_OF",
                  "matchCaseSensitive": false,
                  "normalize": false,
                  "values": [
                    "/pages/*"
                  ]
                }
              }
            ],
            "criteriaMustSatisfy": "all",
            "comments": ""
          },
          {
            "name": "Set x-locale header",
            "children": [],
            "behaviors": [
              {
                "name": "modifyOutgoingRequestHeader",
                "options": {
                  "action": "MODIFY",
                  "standardModifyHeaderName": "OTHER",
                  "newHeaderValue": "fr_CA",
                  "avoidDuplicateHeaders": false,
                  "customHeaderName": "x-locale"
                }
              }
            ],
            "criteria": [],
            "criteriaMustSatisfy": "all",
            "comments": ""
          },
          {
            "name": "Execute Edge Worker",
            "children": [
              {
                "name": "Hashes path caching",
                "children": [],
                "behaviors": [
                  {
                    "name": "caching",
                    "options": {
                      "behavior": "MAX_AGE",
                      "mustRevalidate": true,
                      "ttl": "1d"
                    }
                  },
                  {
                    "name": "cacheTag",
                    "options": {
                      "tag": "{{user.PMUSER_GWP_CONTENT_CACHE_TAG}}"
                    }
                  },
                  {
                    "name": "cacheTag",
                    "options": {
                      "tag": "GWP_RENDERED_CONTENT_TAG"
                    }
                  },
                  {
                    "name": "cacheTagVisible",
                    "options": {
                      "behavior": "PRAGMA_HEADER"
                    }
                  },
                  {
                    "name": "modifyOutgoingRequestHeader",
                    "options": {
                      "action": "ADD",
                      "standardAddHeaderName": "OTHER",
                      "headerValue": "true",
                      "customHeaderName": "X-Hashes-Caching"
                    }
                  }
                ],
                "criteria": [
                  {
                    "name": "matchVariable",
                    "options": {
                      "matchOperator": "IS",
                      "matchWildcard": false,
                      "matchCaseSensitive": true,
                      "variableName": "PMUSER_HASH_REDIRECT_CACHING",
                      "variableExpression": "true"
                    }
                  }
                ],
                "criteriaMustSatisfy": "all",
                "comments": "Caches hashes path responses in akamai cdn cache. Hashes paths are served via cloudfront -> S3"
              }
            ],
            "behaviors": [
              {
                "name": "edgeWorker",
                "options": {
                  "enabled": true,
                  "edgeWorkerId": "86998",
                  "mPulse": false,
                  "createEdgeWorker": "",
                  "mPulseInformation": "",
                  "resourceTier": ""
                }
              },
              {
                "name": "modifyOutgoingRequestHeader",
                "options": {
                  "action": "ADD",
                  "standardAddHeaderName": "OTHER",
                  "headerValue": "true",
                  "customHeaderName": "X-EdgeWorker"
                }
              }
            ],
            "criteria": [
              {
                "name": "requestHeader",
                "options": {
                  "matchOperator": "IS_ONE_OF",
                  "matchWildcardName": false,
                  "matchWildcardValue": false,
                  "matchCaseSensitiveValue": true,
                  "headerName": "EDGE_WORKER_FLOW_ENABLED",
                  "values": [
                    "true"
                  ]
                }
              },
              {
                "name": "matchVariable",
                "options": {
                  "matchOperator": "IS",
                  "matchWildcard": false,
                  "matchCaseSensitive": true,
                  "variableName": "PMUSER_ENABLE_GWP_EDGE_WORKER",
                  "variableExpression": "1"
                }
              }
            ],
            "criteriaMustSatisfy": "all",
            "comments": ""
          }
        ],
        "behaviors": [
          {
            "name": "modifyIncomingRequestHeader",
            "options": {
              "action": "DELETE",
              "standardDeleteHeaderName": "OTHER",
              "customHeaderName": "Authorization"
            }
          },
          {
            "name": "modifyOutgoingRequestHeader",
            "options": {
              "action": "ADD",
              "standardAddHeaderName": "OTHER",
              "headerValue": "Token key=fake",
              "customHeaderName": "Authorization"
            }
          }
        ],
        "criteria": [
          {
            "name": "matchVariable",
            "options": {
              "matchOperator": "IS_ONE_OF",
              "matchWildcard": false,
              "matchCaseSensitive": true,
              "variableName": "PMUSER_ORIGIN_NAME",
              "variableValues": [
                "gwp"
              ]
            }
          }
        ],
        "criteriaMustSatisfy": "all",
        "comments": "Route request to GWP WebOrchestrator Origin and apply applicable child rules."
      },
      {
        "name": "Conditional Origin Group",
        "children": [
          {
            "name": "Maintenance Mode",
            "children": [],
            "behaviors": [
              {
                "name": "origin",
                "options": {
                  "originType": "NET_STORAGE",
                  "netStorage": {
                    "downloadDomainName": "examplegpm.download.akamai.com",
                    "cpCode": 590357,
                    "g2oToken": null
                  }
                }
              },
              {
                "name": "caching",
                "options": {
                  "behavior": "MAX_AGE",
                  "mustRevalidate": false,
                  "ttl": "10m"
                }
              },
              {
                "name": "cacheKeyQueryParams",
                "options": {
                  "behavior": "IGNORE_ALL"
                }
              },
              {
                "name": "cacheError",
                "options": {
                  "enabled": true,
                  "ttl": "31s",
                  "preserveStale": true
                }
              },
              {
                "name": "rewriteUrl",
                "options": {
                  "behavior": "REWRITE",
                  "targetUrl": "/t.example.ca/throttle/maintenance-fr.html"
                }
              }
            ],
            "criteria": [
              {
                "name": "cloudletsOrigin",
                "options": {
                  "originId": "MAINTENANCE"
                }
              }
            ],
            "criteriaMustSatisfy": "all",
            "comments": ""
          },
          {
            "name": "Conditional Origin Definition",
            "children": [],
            "behaviors": [
              {
                "name": "origin",
                "options": {
                  "cacheKeyHostname": "ORIGIN_HOSTNAME",
                  "compress": true,
                  "enableTrueClientIp": true,
                  "forwardHostHeader": "CUSTOM",
                  "httpPort": 80,
                  "originSni": true,
                  "originType": "CUSTOMER",
                  "verificationMode": "CUSTOM",
                  "httpsPort": 443,
                  "hostname": "p.example.ca",
                  "originCertificate": "",
                  "ports": "",
                  "customValidCnValues": [
                    "{{Origin Hostname}}",
                    "{{Forward Host Header}}"
                  ],
                  "originCertsToHonor": "STANDARD_CERTIFICATE_AUTHORITIES",
                  "trueClientIpHeader": "True-Client-IP",
                  "trueClientIpClientSetting": false,
                  "customForwardHostHeader": "t.example.ca",
                  "standardCertificateAuthorities": [
                    "akamai-permissive",
                    "THIRD_PARTY_AMAZON"
                  ],
                  "minTlsVersion": "DYNAMIC",
                  "ipVersion": "IPV4",
                  "tlsVersionTitle": ""
                }
              },
              {
                "name": "cpCode",
                "options": {
                  "value": {
                    "id": 1057255,
                    "description": "t.example.ca",
                    "products": [
                      "Fresca"
                    ],
                    "createdDate": 1591905036000,
                    "cpCodeLimits": {
                      "limit": 928,
                      "currentCapacity": 268,
                      "limitType": "account"
                    },
                    "name": "t.example.ca"
                  }
                }
              }
            ],
            "criteria": [
              {
                "name": "cloudletsOrigin",
                "options": {
                  "originId": "dc1_impot_ca_prod"
                }
              }
            ],
            "criteriaMustSatisfy": "all"
          },
          {
            "name": "contentmesh",
            "children": [],
            "behaviors": [
              {
                "name": "origin",
                "options": {
                  "cacheKeyHostname": "ORIGIN_HOSTNAME",
                  "compress": true,
                  "enableTrueClientIp": true,
                  "forwardHostHeader": "ORIGIN_HOSTNAME",
                  "httpPort": 80,
                  "originSni": true,
                  "originType": "CUSTOMER",
                  "verificationMode": "CUSTOM",
                  "httpsPort": 443,
                  "hostname": "c.example.com",
                  "originCertificate": "",
                  "ports": "",
                  "trueClientIpHeader": "True-Client-IP",
                  "trueClientIpClientSetting": false,
                  "customValidCnValues": [
                    "{{Origin Hostname}}",
                    "{{Forward Host Header}}"
                  ],
                  "originCertsToHonor": "STANDARD_CERTIFICATE_AUTHORITIES",
                  "standardCertificateAuthorities": [
                    "akamai-permissive",
                    "THIRD_PARTY_AMAZON"
                  ],
                  "minTlsVersion": "DYNAMIC",
                  "ipVersion": "IPV4",
                  "tlsVersionTitle": ""
                }
              },
              {
                "name": "cpCode",
                "options": {
                  "value": {
                    "id": 1057255,
                    "description": "t.example.ca",
                    "products": [
                      "Fresca"
                    ],
                    "createdDate": 1591905036000,
                    "cpCodeLimits": {
                      "limit": 928,
                      "currentCapacity": 268,
                      "limitType": "account"
                    },
                    "name": "t.example.ca"
                  }
                }
              },
              {
                "name": "modifyIncomingRequestHeader",
                "options": {
                  "action": "MODIFY",
                  "standardModifyHeaderName": "OTHER",
                  "newHeaderValue": "Token key=fake",
                  "avoidDuplicateHeaders": true,
                  "customHeaderName": "Authorization"
                }
              }
            ],
            "criteria": [
              {
                "name": "cloudletsOrigin",
                "options": {
                  "originId": "contentmesh"
                }
              }
            ],
            "criteriaMustSatisfy": "all",
            "comments": ""
          }
        ],
        "behaviors": [
          {
            "name": "allowCloudletsOrigins",
            "options": {
              "enabled": true,
              "honorBaseDirectory": true,
              "purgeOriginQueryParameter": "originId"
            }
          }
        ],
        "criteria": [],
        "criteriaMustSatisfy": "all"
      }
    ],
    "behaviors": [
      {
        "name": "origin",
        "options": {
          "cacheKeyHostname": "REQUEST_HOST_HEADER",
          "compress": true,
          "enableTrueClientIp": true,
          "forwardHostHeader": "ORIGIN_HOSTNAME",
          "hostname": "w.example.com",
          "httpPort": 80,
          "httpsPort": 443,
          "originSni": true,
          "originType": "CUSTOMER",
          "verificationMode": "CUSTOM",
          "originCertificate": "",
          "ports": "",
          "trueClientIpHeader": "True-Client-IP",
          "trueClientIpClientSetting": false,
          "customValidCnValues": [
            "{{Origin Hostname}}",
            "{{Forward Host Header}}"
          ],
          "originCertsToHonor": "STANDARD_CERTIFICATE_AUTHORITIES",
          "standardCertificateAuthorities": [
            "akamai-permissive"
          ],
          "minTlsVersion": "DYNAMIC",
          "ipVersion": "IPV4",
          "tlsVersionTitle": ""
        }
      },
      {
        "name": "cpCode",
        "options": {
          "value": {
            "id": 1701599,
            "description": "G.example.ca",
            "products": [
              "Fresca"
            ],
            "createdDate": 1726668238000,
            "cpCodeLimits": null,
            "name": "G.example.ca"
          }
        }
      },
      {
        "name": "allowPost",
        "options": {
          "allowWithoutContentLength": false,
          "enabled": true
        }
      },
      {
        "name": "report",
        "options": {
          "logHost": true,
          "logReferer": true,
          "logUserAgent": true,
          "logAcceptLanguage": false,
          "logCookies": "OFF",
          "logCustomLogField": false,
          "logEdgeIP": false,
          "logXForwardedFor": false
        }
      },
      {
        "name": "caching",
        "options": {
          "behavior": "CACHE_CONTROL_AND_EXPIRES",
          "mustRevalidate": false,
          "defaultTtl": "0s",
          "honorPrivate": true,
          "honorMustRevalidate": true,
          "enhancedRfcSupport": false,
          "cacheControlDirectives": ""
        }
      },
      {
        "name": "phasedRelease",
        "options": {
          "enabled": true,
          "cloudletPolicy": {
            "id": 137797,
            "name": "PR_impot_CA_to_Marketing_Platform_clone"
          },
          "label": "pr_impot_ca_to_marketing_platform",
          "populationTitle": "",
          "populationCookieType": "ON_BROWSER_CLOSE",
          "failoverTitle": "",
          "failoverEnabled": false,
          "isSharedPolicy": false
        }
      },
      {
        "name": "edgeRedirector",
        "options": {
          "enabled": true,
          "cloudletPolicy": {
            "id": 149193,
            "name": "prod_impot_ca_redirects"
          },
          "isSharedPolicy": false
        }
      },
      {
        "name": "siteShield",
        "options": {
          "ssmap": {
            "name": "ttcom_prod_site_shield (s2038.akamaiedge.net)",
            "value": "s2038.akamaiedge.net",
            "srmap": "Example-Inc-e3321.akasrg.akamai.com",
            "hasMixedHosts": false,
            "src": "PREVIOUS_MAP"
          }
        }
      },
      {
        "name": "rewriteUrl",
        "options": {
          "behavior": "REGEX_REPLACE",
          "keepQueryString": true,
          "matchMultiple": true,
          "matchRegex": "([.|]+)",
          "targetRegex": "%7C"
        }
      },
      {
        "name": "setVariable",
        "options": {
          "valueSource": "EXTRACT",
          "transform": "NONE",
          "variableName": "PMUSER_GEO_COUNTRY_CODE",
          "extractLocation": "EDGESCAPE",
          "locationId": "COUNTRY_CODE"
        }
      },
      {
        "name": "setVariable",
        "options": {
          "valueSource": "EXTRACT",
          "transform": "NONE",
          "variableName": "PMUSER_GEO_PROVINCE_CODE",
          "extractLocation": "EDGESCAPE",
          "locationId": "REGION_CODE"
        }
      },
      {
        "name": "responseCookie",
        "options": {
          "enabled": true,
          "type": "FIXED",
          "defaultDomain": true,
          "defaultPath": false,
          "expires": "ON_BROWSER_CLOSE",
          "sameSite": "NONE",
          "secure": true,
          "httpOnly": false,
          "cookieName": "AKES_GEO",
          "value": "{{user.PMUSER_GEO_COUNTRY_CODE}}~{{user.PMUSER_GEO_PROVINCE_CODE}}",
          "path": "/"
        }
      },
      {
        "name": "setVariable",
        "options": {
          "valueSource": "EXPRESSION",
          "transform": "NONE",
          "variableName": "PMUSER_ORIGIN_NAME",
          "variableValue": "gwp"
        }
      },
      {
        "name": "datastream",
        "options": {
          "streamType": "LOG",
          "logStreamTitle": "",
          "logEnabled": true,
          "logStreamName": [
            "66217"
          ],
          "samplingPercentage": 100,
          "collectMidgressTraffic": false
        }
      }
    ],
    "options": {
      "is_secure": true
    },
    "variables": [
      {
        "name": "PMUSER_PRIORITY_CODE",
        "value": "",
        "description": "",
        "hidden": false,
        "sensitive": false
      },
      {
        "name": "PMUSER_ORIGIN_NAME",
        "value": "",
        "description": "",
        "hidden": false,
        "sensitive": false
      },
      {
        "name": "PMUSER_GWP_CONTENT_CACHE_TAG",
        "value": "",
        "description": "Extracts cache tag value for hashes path caching",
        "hidden": false,
        "sensitive": false
      },
      {
        "name": "PMUSER_HASH_REDIRECT_CACHING",
        "value": "",
        "description": "Boolean flag to decide whether content should be cached",
        "hidden": false,
        "sensitive": false
      },
      {
        "name": "PMUSER_ENABLE_GWP_EDGE_WORKER",
        "value": "0",
        "description": "Variable used to decide if edge worker to be used to serve",
        "hidden": false,
        "sensitive": false
      },
      {
        "name": "PMUSER_GEO_PROVINCE_CODE",
        "value": "QC",
        "description": "",
        "hidden": false,
        "sensitive": false
      },
      {
        "name": "PMUSER_GEO_COUNTRY_CODE",
        "value": "CA",
        "description": "",
        "hidden": false,
        "sensitive": false
      },
      {
        "name": "PMUSER_HOST",
        "value": "",
        "description": "",
        "hidden": false,
        "sensitive": false
      },
      {
        "name": "PMUSER_FILENAME",
        "value": "",
        "description": "",
        "hidden": false,
        "sensitive": false
      },
      {
        "name": "PMUSER_COUNTRY",
        "value": "",
        "description": "",
        "hidden": true,
        "sensitive": false
      }
    ],
    "customOverride": {
      "overrideId": "cbo_465903994",
      "name": "embargo_geo_blocking "
    },
    "comments": "The behaviors in the Default Rule apply to all requests for the property hostname(s) unless another rule overrides the Default Rule settings."
  },
  "errors": [
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/generic_behavior_issue.invalid_data_stream_selected_all_deleted",
      "errorLocation": "#/rules/behaviors/13/options/logStreamName",
      "detail": "Either all the associated streams are deleted, or you are missing DataStream permissions. Replace the streams and make sure you have proper DataStream access, or remove the DataStream behavior from the configuration."
    }
  ],
  "warnings": [
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/validation_message.ssl_custom_warning_test_staging",
      "errorLocation": "#/rules/behaviors/0",
      "detail": "If you are changing your `Origin Server` SSL Certificate Verification settings it is strongly recommended that you test on Staging before activating on Production. Failure to test on Staging may result in a service outage."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/generic_behavior_issue.all_methods_on_ps",
      "errorLocation": "#/rules/behaviors/2",
      "detail": "The _Allow All Methods on Parent Servers_ behavior must also be added for proper functionality"
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/validation_message.warn_regex",
      "errorLocation": "#/rules/behaviors/8",
      "detail": "Format validation is not applied to the input fields when using the Regular Expression Replacement option in `Modify Outgoing Request Path`. Please test thoroughly on Akamai's Staging Network when using this option. Do not hesitate to reach out to an Akamai Technical representative if you are uncertain about how this option is used."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/cannot_validate",
      "errorLocation": "#/rules/behaviors/11/options/value",
      "detail": "The input to option Value of `Set Response Cookie` cannot be validated because of variable expression usage. Because of the use of variables, the value of the option is only known at runtime."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/validation_message.ssl_custom_warning_test_staging",
      "errorLocation": "#/rules/children/1/behaviors/0",
      "detail": "If you are changing your `Origin Server` SSL Certificate Verification settings it is strongly recommended that you test on Staging before activating on Production. Failure to test on Staging may result in a service outage."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/cannot_validate",
      "errorLocation": "#/rules/children/3/children/0/behaviors/1/options/netStoragePath",
      "detail": "The input to option Modified Path of `Site Failover` cannot be validated because of variable expression usage. Because of the use of variables, the value of the option is only known at runtime."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/need_condition",
      "errorLocation": "#/rules/children/3/children/0/behaviors/1",
      "detail": "To ensure the `Site Failover` behavior works correctly, you should use it within a match such as Response Status Code or Origin Timeout."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/need_feature",
      "errorLocation": "#/rules/children/6/behaviors/0",
      "detail": "When your `Origin Server` is set to NetStorage, enable Cache HTTP Error Responses with a TTL of at least 30 seconds."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/need_feature",
      "errorLocation": "#/rules/children/7/behaviors/0",
      "detail": "The Cache Key Query Parameters behavior should be set to ignore all when a NetStorage `Origin Server` is used. Netstorage does not honor query strings, so you should set this to avoid duplicate cache keys for the same object."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/need_feature",
      "errorLocation": "#/rules/children/7/behaviors/0",
      "detail": "When your `Origin Server` is set to NetStorage, enable Cache HTTP Error Responses with a TTL of at least 30 seconds."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/cannot_validate",
      "errorLocation": "#/rules/children/11/children/2/behaviors/0/options/value",
      "detail": "The input to option Value of `Set Response Cookie` cannot be validated because of variable expression usage. Because of the use of variables, the value of the option is only known at runtime."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/cannot_validate",
      "errorLocation": "#/rules/children/11/children/3/behaviors/0/options/value",
      "detail": "The input to option Value of `Set Response Cookie` cannot be validated because of variable expression usage. Because of the use of variables, the value of the option is only known at runtime."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/validation_message.ssl_custom_warning_test_staging",
      "errorLocation": "#/rules/children/12/behaviors/0",
      "detail": "If you are changing your `Origin Server` SSL Certificate Verification settings it is strongly recommended that you test on Staging before activating on Production. Failure to test on Staging may result in a service outage."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/validation_message.general_warning",
      "errorLocation": "#/rules/children/15/children/0/children/0/criteria/0",
      "detail": "Matching on `Request Type` requires thorough understanding of the way Akamai Edge servers process requests.  If you are unsure about how this will affect your property, please contact your Akamai Technical representative, and please test thoroughly on staging before activating on production."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/incompatible_condition",
      "errorLocation": "#/rules/children/15/children/1/behaviors/0",
      "detail": "Using the `Origin Server` behavior within a match on `Request Header` will make it impossible to use the Content Control Utility to purge by URL. Please contact your Akamai Representative to explore alternative methods for making your content purgeable"
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/incompatible_condition",
      "errorLocation": "#/rules/children/15/children/1/behaviors/0",
      "detail": "Using the `Origin Server` behavior within a match on `Request Header` will make it impossible to use the Content Control Utility to purge by URL. Please contact your Akamai Representative to explore alternative methods for making your content purgeable"
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/validation_message.ssl_custom_warning_test_staging",
      "errorLocation": "#/rules/children/15/children/1/behaviors/0",
      "detail": "If you are changing your `Origin Server` SSL Certificate Verification settings it is strongly recommended that you test on Staging before activating on Production. Failure to test on Staging may result in a service outage."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/validation_message.general_warning",
      "errorLocation": "#/rules/children/15/children/1/children/0/criteria/0",
      "detail": "Matching on `Request Type` requires thorough understanding of the way Akamai Edge servers process requests.  If you are unsure about how this will affect your property, please contact your Akamai Technical representative, and please test thoroughly on staging before activating on production."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/incompatible_condition",
      "errorLocation": "#/rules/children/15/children/2/behaviors/0",
      "detail": "Using the `Origin Server` behavior within a match on `Request Header` will make it impossible to use the Content Control Utility to purge by URL. Please contact your Akamai Representative to explore alternative methods for making your content purgeable"
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/incompatible_condition",
      "errorLocation": "#/rules/children/15/children/2/behaviors/0",
      "detail": "Using the `Origin Server` behavior within a match on `Request Header` will make it impossible to use the Content Control Utility to purge by URL. Please contact your Akamai Representative to explore alternative methods for making your content purgeable"
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/validation_message.ssl_custom_warning_test_staging",
      "errorLocation": "#/rules/children/15/children/2/behaviors/0",
      "detail": "If you are changing your `Origin Server` SSL Certificate Verification settings it is strongly recommended that you test on Staging before activating on Production. Failure to test on Staging may result in a service outage."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/validation_message.general_warning",
      "errorLocation": "#/rules/children/15/children/2/children/0/criteria/0",
      "detail": "Matching on `Request Type` requires thorough understanding of the way Akamai Edge servers process requests.  If you are unsure about how this will affect your property, please contact your Akamai Technical representative, and please test thoroughly on staging before activating on production."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/cannot_validate",
      "errorLocation": "#/rules/children/15/children/4/behaviors/0/options/targetUrl",
      "detail": "The input to option Replace with of `Modify Outgoing Request Path` cannot be validated because of variable expression usage. Because of the use of variables, the value of the option is only known at runtime."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/cannot_validate",
      "errorLocation": "#/rules/children/15/children/6/children/0/behaviors/1/options/tag",
      "detail": "The input to option Tag Name of `Cache Tag` cannot be validated because of variable expression usage. Because of the use of variables, the value of the option is only known at runtime."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/need_feature",
      "errorLocation": "#/rules/children/16/children/0/behaviors/0",
      "detail": "When your `Origin Server` is set to NetStorage, enable Cache HTTP Error Responses with a TTL of at least 30 seconds."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/validation_message.ssl_custom_warning_test_staging",
      "errorLocation": "#/rules/children/16/children/1/behaviors/0",
      "detail": "If you are changing your `Origin Server` SSL Certificate Verification settings it is strongly recommended that you test on Staging before activating on Production. Failure to test on Staging may result in a service outage."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/validation_message.ssl_custom_warning_test_staging",
      "errorLocation": "#/rules/children/16/children/2/behaviors/0",
      "detail": "If you are changing your `Origin Server` SSL Certificate Verification settings it is strongly recommended that you test on Staging before activating on Production. Failure to test on Staging may result in a service outage."
    },
    {
      "type": "https://problems.luna.akamaiapis.net/papi/v0/validation/advanced_override_metadata_enabled",
      "errorLocation": "#/rules",
      "detail": "This property contains <strong>advanced override metadata</strong>. This will potentially override any of the rule configurations that have been set above."
    },
    {
      "title": "Unstable rule format",
      "type": "https://problems.luna.akamaiapis.net/papi/v0/unstable_rule_format",
      "detail": "This property is using `latest` rule format, which is designed to reflect interface changes immediately. We suggest converting the property to a stable rule format such as `v2025-02-18` to minimize the risk of interface changes breaking your API client program.",
      "currentRuleFormat": "latest",
      "suggestedRuleFormat": "v2025-02-18"
    }
  ],
  "ruleFormat": "latest",
  "comments": "Blog full migration",
  "assetId": "10807565"
}
""",
    strict=False,
)
