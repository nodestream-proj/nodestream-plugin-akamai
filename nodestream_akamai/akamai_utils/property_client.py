import itertools
import logging
import re
from typing import Any, List, Tuple

from jsonpath_ng.ext import parse

from .client import AkamaiApiClient
from .model import (
    AkamaiPropertyResponse,
    EdgeHost,
    Origin,
    PropertyDescription,
    PropertyRuleRecord,
)

PATH_AND = " AND "

logger = logging.getLogger(__name__)


CLOUDLET_TYPES = [
    "applicationLoadBalancer",
    "apiPrioritization",
    "audienceSegmentation",
    "phasedRelease",
    "edgeRedirector",
    "forwardRewrite",
    "requestControl",
    "visitorPrioritization",
    "virtualWaitingRoom",
]

# Define criteria to look at
MATCH_TYPES = ["path", "hostname", "cloudletsOrigin"]

# Define negative criterion matches
NEGATIVE_OPERATORS = ["DOES_NOT_MATCH_ONE_OF", "IS_NOT_ONE_OF"]


def getPolicySetPrefix(options):
    if "policyTokenDefault" in options:
        return options["policyTokenDefault"] + "-"
    if "policyToken" in options:
        return options["policyToken"] + "-"
    return ""


def extractOrigin(behavior):
    if behavior.get("name") == "origin":
        originOptions = behavior["options"]
        match originOptions.get("originType"):
            case "CUSTOMER":
                return Origin(name=originOptions.get("hostname"))
            case "NET_STORAGE":
                return Origin(
                    name=originOptions["netStorage"].get("downloadDomainName")
                )
            case "MEDIA_SERVICE_LIVE":
                return Origin(name=originOptions.get("mslorigin"))
            case _:
                return None
    return None


def flattenOrigins(origin):
    flattened = list(
        itertools.chain(
            (
                Origin(name=origin["name"], path=path)
                for path in origin.get("paths", [])
            ),
            (
                Origin(name=origin["name"], hostname=hostname)
                for hostname in origin.get("hostnames", [])
            ),
            (
                Origin(name=origin["name"], conditional_origin=conditionalOrigin)
                for conditionalOrigin in origin.get("conditional_origins", [])
            ),
        )
    )
    if flattened:
        return flattened

    return [Origin(name=origin["name"])]


class AkamaiPropertyClient(AkamaiApiClient):
    def __init__(
        self,
        base_url,
        client_token,
        client_secret,
        access_token,
        account_key=None,
    ):
        super().__init__(
            base_url,
            client_token,
            client_secret,
            access_token,
            account_key,
        )
        self.logger = logging.getLogger(self.__class__.__name__)

    @property
    def headers(self):
        return {"PAPI-Use-Prefixes": "false"}

    def contractsByGroup(self) -> List[Tuple[str, str]]:
        groupsListApiPath = "/papi/v1/groups"
        responseJson = self._get_api_from_relative_path(
            groupsListApiPath, headers=self.headers
        )
        return [
            (group["groupId"], contractId)
            for group in responseJson["groups"]["items"]
            for contractId in group["contractIds"]
        ]

    def listContracts(self) -> List[str]:
        contractsListApiPath = "/papi/v1/contracts"
        responseJson = self._get_api_from_relative_path(
            contractsListApiPath, headers=self.headers
        )
        return responseJson["contracts"]["items"]

    def propertyIdsForContractGroup(self, groupId: str, contractId: str) -> List[str]:
        propertyListApiPath = "/papi/v1/properties"
        queryParams = {
            "groupId": groupId,
            "contractId": contractId,
        }
        responseJson = self._get_api_from_relative_path(
            propertyListApiPath, params=queryParams, headers=self.headers
        )
        return [prop["propertyId"] for prop in responseJson["properties"]["items"]]

    def get_rule_tree(
        self, property_id: str, version: int, contract_id=None, group_id=None
    ):
        ruleTreeApiPath = f"/papi/v1/properties/{property_id}/versions/{version}/rules"
        params = {}
        if contract_id is not None and group_id is not None:
            params = {"contractId": contract_id, "groupId": group_id}
        return self._get_api_from_relative_path(
            ruleTreeApiPath, params=params, headers=self.headers
        )

    def getProperty(self, propertyId: str, contractId=None, groupId=None):
        propertyPath = f"/papi/v1/properties/{propertyId}"
        params = {}
        if contractId is not None and groupId is not None:
            params = {"contractId": contractId, "groupId": groupId}
        return self._get_api_from_relative_path(
            propertyPath, params=params, headers=self.headers
        )["properties"]["items"][0]

    def describePropertyHostnames(
        self, propertyId: str, version: int, contractId=None, groupId=None
    ):
        hostsApiPath = f"/papi/v1/properties/{propertyId}/versions/{version}/hostnames"
        params = {}
        if contractId is not None and groupId is not None:
            params = {"contractId": contractId, "groupId": groupId}
        hostsApiResponse = self._get_api_from_relative_path(
            hostsApiPath, params=params, headers=self.headers
        )
        return [
            EdgeHost(name=edgeHost["cnameFrom"])
            for edgeHost in hostsApiResponse["hostnames"]["items"]
        ]

    def pullHostEntries(
        self, propertyId: str, versions: set
    ) -> tuple[set[Origin], set[Any], set[EdgeHost]]:
        origins = set()
        edgeRedirectorPolicies = set()
        hostnames = set()
        for version in versions:
            if version is None:
                continue
            ruleTree = self.get_rule_tree(propertyId, version)
            origins.update(self.searchRuleTreeForOrigins(ruleTree))
            edgeRedirectorPolicies.update()
            hostnames.update(self.describePropertyHostnames(propertyId, version))
        return origins, edgeRedirectorPolicies, hostnames

    def describePropertyById(self, propertyId: str) -> PropertyDescription:
        describePropertyApiPath = f"/papi/v1/properties/{propertyId}"
        propertyDescription = self._get_api_from_relative_path(
            describePropertyApiPath, headers=self.headers
        )["properties"]["items"][0]
        propertyName = propertyDescription["propertyName"]
        productionVersionNumber = propertyDescription["productionVersion"]
        stagingVersionNumber = propertyDescription["stagingVersion"]
        origins, _, hostnames = self.pullHostEntries(
            propertyId, {productionVersionNumber, stagingVersionNumber}
        )

        return PropertyDescription(
            id=propertyId,
            name=propertyName,
            origins=list(origins),
            hostnames=list(hostnames),
        )

    def describePropertyByDict(
        self, prop: AkamaiPropertyResponse, version: int
    ) -> PropertyDescription:
        # Get rule tree
        ruleTree = self.get_rule_tree(
            property_id=prop.propertyId,
            version=version,
            contract_id=prop.contractId,
            group_id=prop.groupId,
        )
        ruleTree["assetId"] = prop.assetId

        # Update origins
        origins = self.collateOriginsWithCriteria(ruleTree["rules"])
        hostnames = [
            EdgeHost(name=hostname["cnameFrom"]) for hostname in prop.hostnames
        ]

        # Cloudlets
        cloudletPolicies = self.searchRuleTreeForCloudlets(ruleTree=ruleTree["rules"])

        # Specific data for Edge Redirector, filter for legacy only
        edgeRedirectorPolicies = self.searchRuleTreeForCloudlet(
            ruleTree=ruleTree["rules"], behaviorName="edgeRedirector", shared=False
        )

        # IVM
        imageManagerPolicysets = self.searchRuleTreeForIvm(ruleTree=ruleTree)

        # EdgeWorkers
        edgeworkerIds = self.searchRuleTreeForEdgeWorkers(ruleTree=ruleTree["rules"])

        # Siteshield
        siteshieldMaps = self.searchRuleTreeForSiteshield(ruleTree=ruleTree["rules"])

        # CP Codes
        cpCodes = self.searchRuleTreeForCpCodes(ruleTree=ruleTree["rules"])

        return PropertyDescription(
            id=prop.propertyId,
            name=prop.propertyName,
            version=version,
            rule_format=ruleTree["ruleFormat"],
            origins=origins,
            cloudlet_policies=cloudletPolicies,
            edge_redirector_policies=edgeRedirectorPolicies,
            image_manager_policysets=imageManagerPolicysets,
            edgeworker_ids=edgeworkerIds,
            siteshield_maps=siteshieldMaps,
            hostnames=hostnames,
            deeplink=prop.deeplink,
            cp_codes=cpCodes,
        )

    def searchAllProperties(self):
        query = "$.name"
        searchPath = "/papi/v1/bulk/rules-search-requests-synch"
        requestBody = {"bulkSearchQuery": {"syntax": "JSONPATH", "match": query}}
        return self._post_api_from_relative_path(path=searchPath, body=requestBody)

    def listAccountHostnames(self, network="PRODUCTION"):
        listHostnamesPath = f"/papi/v1/hostnames?network={network}&offset=0&limit=999"
        result = self._get_api_from_relative_path(path=listHostnamesPath)
        hostnames = result["hostnames"]["items"]
        while "nextLink" in result["hostnames"]:
            nextLink = result["hostnames"]["nextLink"]
            result = self._get_api_from_relative_path(path=nextLink)
            hostnames.extend(result["hostnames"]["items"])

        return hostnames

    def list_all_properties(self) -> List[AkamaiPropertyResponse] | None:
        try:
            hostnames = self.listAccountHostnames()
        except Exception as err:
            logger.exception("Failed to list property hostnames: %s", err)
            return None

        propertyIds = {hostname["propertyId"] for hostname in hostnames}
        return [
            self.buildPropertyResponse(propertyId, hostnames)
            for propertyId in propertyIds
        ]

    def searchRuleTreeForOrigins(self, ruleTree) -> set[Origin]:
        behaviors = ruleTree.get("behaviors", [])
        children = ruleTree.get("children", [])
        origins = set()

        for childRuleTree in children:
            for childOrigin in self.searchRuleTreeForOrigins(childRuleTree):
                origins.add(childOrigin)

        for behavior in behaviors:
            extracted = extractOrigin(behavior)
            if extracted:
                origins.add(extracted)

        return set(origins)

    def collateOriginsWithCriteria(self, rules) -> list[Origin]:
        """
        This function will find all Origin behaviours in a property and collate any relevant criteria
        into accompanying Lists.
        """
        jsonpathExpression = parse('$..behaviors[?(@.name=="origin")]')
        jsonpathResult = jsonpathExpression.find(rules)
        # Parse matched jsonpath behaviours
        origins = [
            self.fetchOriginsAtJsonpath(jsonpathPath, rules)
            for jsonpathPath in jsonpathResult
        ]

        # Expand to one origin hostname/path combo per object to simplify the pipeline config and avoid
        # nested looping
        return list(
            itertools.chain.from_iterable(flattenOrigins(origin) for origin in origins)
        )

    def fetchOriginsAtJsonpath(self, jsonpathPath, rules):
        originHost, locationElements = self.parseOriginSearch(jsonpathPath, rules)
        parentLocation = ""
        combinedRulePaths = []
        combinedRuleHosts = []
        combinedRuleConditionalOrigins = []
        for location in locationElements:
            locationResults = self.parseOriginLocation(location, parentLocation, rules)
            if len(locationResults.get("path", [])) > 0:
                combinedRulePaths.append(locationResults["path"])
            if len(locationResults.get("hostname", [])) > 0:
                combinedRuleHosts.append(locationResults["hostname"])
            if len(locationResults.get("cloudletsOrigin", [])) > 0:
                combinedRuleConditionalOrigins.append(
                    locationResults["cloudletsOrigin"]
                )
            parentLocation = location
        # Combine results into single list with boolean AND between parent and child
        output = {"name": originHost}

        if combinedRulePaths:
            output["paths"] = [
                PATH_AND.join(pathProduct)
                for pathProduct in itertools.product(*combinedRulePaths)
            ]
        if combinedRuleHosts:
            output["hostnames"] = [
                PATH_AND.join(hostProduct)
                for hostProduct in itertools.product(*combinedRuleHosts)
            ]

        if combinedRuleConditionalOrigins:
            output["conditional_origins"] = [
                PATH_AND.join(conditionalOriginProduct)
                for conditionalOriginProduct in itertools.product(
                    *combinedRuleConditionalOrigins
                )
            ]

        return output

    def parseOriginSearch(self, path, rules):
        """
        This function parses jsonpath origin search results into a hostname
        and location elements List
        """
        self.logger.debug("parseOriginSearch")
        originLocation = str(path.full_path)
        ruleBase = re.sub(r"behaviors.\[\d+]", "", originLocation)
        originHost = "ERROR"  # Host should be renamed

        # Extract origin behaviour itself and append hostname to list based on origin type
        originBehaviorMatch = parse(originLocation)
        originSearch = originBehaviorMatch.find(rules)
        originBehavior = originSearch[0].value
        if "hostname" in originBehavior["options"]:
            originHost = originBehavior["options"]["hostname"]
        elif "netStorage" in originBehavior["options"]:
            originHost = originBehavior["options"]["netStorage"]["downloadDomainName"]
        elif "mslorigin" in originBehavior["options"]:
            originHost = originBehavior["options"]["mslorigin"]

        # Split JSONPATH into children[X] elements so we can iterate down the path
        locationElements = re.findall(r"children\.\[\d+]", ruleBase)
        return originHost, locationElements

    def parseOriginLocation(self, ruleLocationInput, parentLocation, rules):
        """
        This function parses origin locations to extract path matches, hostname matches
        and Conditional Origin IDs
        """
        self.logger.debug(
            "parseOriginLocation(ruleLocation=%s, parentLocation=%s)",
            ruleLocationInput,
            parentLocation,
        )
        # Construct rule location from element and optionally parent path
        if parentLocation != "":
            ruleLocation = parentLocation + "." + ruleLocationInput
        else:
            ruleLocation = ruleLocationInput

        ruleMatch = parse(ruleLocation)
        ruleSearch = ruleMatch.find(rules)

        if ruleSearch is None or len(ruleSearch) == 0:
            self.logger.warning("No rule found at position '%s'", ruleLocation)
            return {}

        # Extract rule by JSONPATH
        rule = ruleSearch[0].value

        # Instantiate results
        criteriaResults = {}
        ruleResults = {matchType: [] for matchType in MATCH_TYPES}

        for matchType in MATCH_TYPES:
            criteriaResults[matchType] = []
            criterionResults = {matchType: [] for matchType in MATCH_TYPES}

            # Parse criteria and create list of lists of path matches
            for ruleCriterion in rule["criteria"]:
                criterionResults[matchType] = []

                if ruleCriterion["name"] == matchType:
                    criterionOptions = ruleCriterion["options"]
                    for value in criterionOptions.get("values", []):
                        if criterionOptions.get("matchOperator") in NEGATIVE_OPERATORS:
                            value = "!" + value
                        criterionResults[matchType].append(value)
                    if "originId" in criterionOptions:
                        criterionResults[matchType].append(criterionOptions["originId"])

                if len(criterionResults[matchType]) > 0:
                    criteriaResults[matchType].append(criterionResults[matchType])

            if len(criteriaResults[matchType]) > 0:
                # Collate path matches into a list of combinations, based on criteria setting
                if len(criteriaResults[matchType]) == 1:
                    ruleResults[matchType] = criteriaResults[matchType][0]
                else:
                    if rule["criteriaMustSatisfy"] == "all":
                        # If using ALL option we must create boolean combos
                        ruleProduct = itertools.product(*criteriaResults[matchType])
                        for product in ruleProduct:
                            ruleResults[matchType].append(" AND ".join(product))
                    else:
                        for result in criteriaResults[matchType]:
                            ruleResults[matchType].extend(result)
        return ruleResults

    def searchRuleTreeForBehavior(self, ruleTree, behaviorName):
        self.logger.debug("searchRuleTreeForBehavior(behaviorName=%s)", behaviorName)
        jsonpathExpression = parse(
            '$..behaviors[?(@.name=="{b}")]'.format(b=behaviorName)
        )
        jsonpathResult = jsonpathExpression.find(ruleTree)

        return [match.value for match in jsonpathResult]

    def searchRuleTreeForEdgeRedirector(self, ruleTree):
        return self.searchRuleTreeForCloudlet(ruleTree, "edgeRedirector")

    def searchRuleTreeForCloudlet(self, ruleTree, behaviorName, shared=None):
        # If shared is None, both shared and legacy behaviors will be matched
        instances = self.searchRuleTreeForBehavior(ruleTree, behaviorName)
        policyIds = []
        for behavior in instances:
            if behavior["options"]["enabled"]:
                if behavior["options"].get("isSharedPolicy"):
                    # Skip this if shared is False
                    if not shared:
                        continue
                    policyId = behavior["options"]["cloudletSharedPolicy"]
                else:
                    # Skip this if shared is True
                    if shared:
                        continue
                    policyId = behavior["options"]["cloudletPolicy"]["id"]
                policyIds.append(policyId)

        return list(set(policyIds))

    def searchRuleTreeForCloudlets(self, ruleTree):
        instances = []
        for cloudletType in CLOUDLET_TYPES:
            instances.extend(self.searchRuleTreeForBehavior(ruleTree, cloudletType))
        policyIds = []
        for behavior in instances:
            if behavior["options"]["enabled"]:
                if behavior["options"].get("isSharedPolicy"):
                    policyId = behavior["options"]["cloudletSharedPolicy"]
                else:
                    policyId = behavior["options"]["cloudletPolicy"]["id"]
                policyIds.append(policyId)

        return list(set(policyIds))

    def searchRuleTreeForSiteshield(self, ruleTree):
        instances = self.searchRuleTreeForBehavior(ruleTree, "siteShield")
        return [siteshield["options"]["ssmap"]["value"] for siteshield in instances]

    def searchRuleTreeForIvm(self, ruleTree):
        imageInstances = self.searchRuleTreeForBehavior(ruleTree, "imageManager")
        videoInstances = self.searchRuleTreeForBehavior(ruleTree, "imageManagerVideo")
        instances = imageInstances + videoInstances

        for instance in instances:
            # Need to work out policySet if using default or custom options
            options = instance["options"]
            if "policySet" not in options:
                policySetPrefix = getPolicySetPrefix(options)
                policySet = f"{policySetPrefix}{ruleTree['assetId']}"
                if instance["name"] == "imageManagerVideo":
                    policySet += "-v"
                options["policySet"] = policySet

        policySets = []
        for behavior in instances:
            policySets.append(behavior["options"]["policySet"])

        return list(set(policySets))

    def searchRuleTreeForEdgeWorkers(self, ruleTree):
        instances = self.searchRuleTreeForBehavior(ruleTree, "edgeWorker")
        edgeworkerIds = []
        for behavior in instances:
            if (
                "edgeWorkerId" in behavior["options"]
                and behavior["options"]["edgeWorkerId"]
            ):
                edgeworkerIds.append(int(behavior["options"]["edgeWorkerId"]))

        return list(set(edgeworkerIds))

    def searchRuleTreeForCpCodes(self, ruleTree):
        instances = self.searchRuleTreeForBehavior(ruleTree, "cpCode")
        cpcodeIds = []
        for behavior in instances:
            if "value" in behavior["options"] and "id" in behavior["options"]["value"]:
                cpcodeIds.append(int(behavior["options"]["value"]["id"]))

        return list(set(cpcodeIds))

    # ── Rule-level extraction (Proxy schema) ──────────────────────────

    SECURITY_BEHAVIOR_MAP = {
        "edgeAuth": "AKAMAI_EDGE_AUTH",
        "tokenAuth": "AKAMAI_TOKEN_AUTH",
        "siteShield": "AKAMAI_SITE_SHIELD",
        "requestControl": "AKAMAI_REQUEST_CONTROL",
    }

    def extractOutboundPath(self, behaviors: list) -> tuple:
        """Return (outboundPath, baseDirectory) from a rule's behavior list.

        outboundPath encodes the rewriteUrl transformation as a human-readable
        string so the graph captures what path the origin actually receives:

          REPLACE   → "REPLACE:<match>→<targetPath>"
          REMOVE    → "REMOVE:<match>"
          REWRITE   → "REWRITE:<targetUrl>"
          PREPEND   → "PREPEND:<targetPathPrepend>"
          REGEX_REPLACE → "REGEX:<matchRegex>→<targetRegex>"

        baseDirectory is the unconditional base path prefix from the
        baseDirectory behavior (must begin and end with /).

        Both default to None when the respective behavior is absent.
        """
        outboundPath = None
        baseDirectory = None

        for behavior in behaviors:
            behaviorName = behavior.get("name", "")
            options = behavior.get("options", {})

            if behaviorName == "rewriteUrl" and outboundPath is None:
                mode = options.get("behavior", "")
                if mode == "REPLACE":
                    outboundPath = f"REPLACE:{options.get('match','')}→{options.get('targetPath','')}"
                elif mode == "REMOVE":
                    outboundPath = f"REMOVE:{options.get('match','')}"
                elif mode == "REWRITE":
                    outboundPath = f"REWRITE:{options.get('targetUrl','')}"
                elif mode == "PREPEND":
                    outboundPath = f"PREPEND:{options.get('targetPathPrepend','')}"
                elif mode == "REGEX_REPLACE":
                    outboundPath = f"REGEX:{options.get('matchRegex','')}→{options.get('targetRegex','')}"

            elif behaviorName == "baseDirectory" and baseDirectory is None:
                baseDirectory = options.get("value")

        return outboundPath, baseDirectory

    def extractSecurityBehaviors(self, behaviors: list) -> list:
        """Return normalized security behavior names from a rule's behavior list.

        Only behaviors that are explicitly enabled (or have no ``enabled`` key,
        which implies always-on) are included.
        """
        result = []
        for behavior in behaviors:
            mapped = self.SECURITY_BEHAVIOR_MAP.get(behavior.get("name", ""))
            if mapped and behavior.get("options", {}).get("enabled", True):
                result.append(mapped)
        return result

    def extractRuleCriteria(self, rule: dict) -> tuple:
        """Return (pathCriteria, hostnameCriteria, conditionalOriginId) for one rule.

        pathCriteria and hostnameCriteria are List[str] where each element is a
        single pattern — positive or !-negated.  They are NOT joined with AND so
        that callers can pass them directly to micromatch as a pattern array.

        conditionalOriginId is the cloudletsOrigin originId if present, else None.
        """
        pathCriteria = []
        hostnameCriteria = []
        conditionalOriginId = None

        for criterion in rule.get("criteria", []):
            criterionName = criterion["name"]
            options = criterion.get("options", {})
            isNegative = options.get("matchOperator") in NEGATIVE_OPERATORS

            if criterionName == "path":
                for value in options.get("values", []):
                    pathCriteria.append(f"!{value}" if isNegative else value)
            elif criterionName == "hostname":
                for value in options.get("values", []):
                    hostnameCriteria.append(f"!{value}" if isNegative else value)
            elif criterionName == "cloudletsOrigin":
                # originId is a scalar, not a list
                originId = options.get("originId")
                if originId:
                    conditionalOriginId = originId

        return pathCriteria, hostnameCriteria, conditionalOriginId

    def resolveOriginFromBehaviors(
        self,
        behaviors: list,
        inheritedOriginHostname: str | None,
        inheritedOriginType: str | None,
    ) -> tuple[str | None, str | None]:
        """Return (originHostname, originType) for this rule.

        Own origin declaration takes precedence over inherited values.
        """
        for behavior in behaviors:
            extracted = extractOrigin(behavior)
            if extracted and extracted.name is not None:
                return extracted.name, behavior.get("options", {}).get("originType")
        return inheritedOriginHostname, inheritedOriginType

    def resolveOutboundPathFromBehaviors(
        self,
        behaviors: list,
        inheritedOutboundPath: str | None,
        inheritedBaseDirectory: str | None,
    ) -> tuple[str | None, str | None]:
        """Return (outboundPath, baseDirectory) for this rule.

        Own declaration takes precedence over inherited values.
        """
        ownOutboundPath, ownBaseDirectory = self.extractOutboundPath(behaviors)
        outboundPath = (
            ownOutboundPath if ownOutboundPath is not None else inheritedOutboundPath
        )
        baseDirectory = (
            ownBaseDirectory if ownBaseDirectory is not None else inheritedBaseDirectory
        )
        return outboundPath, baseDirectory

    def extractRuleRecords(
        self,
        rule: dict,
        propertyId: str,
        propertyName: str,
        version: int,
        deeplink: str,
        depth: int = 0,
        inheritedPathCriteria: list | None = None,
        inheritedHostnameCriteria: list | None = None,
        inheritedOriginHostname: str | None = None,
        inheritedOriginType: str | None = None,
        inheritedOutboundPath: str | None = None,
        inheritedBaseDirectory: str | None = None,
    ) -> list:
        """Recursively extract PropertyRuleRecord objects from a rule tree node.

        Criteria from ancestor rules are prepended so that each record carries
        the full effective criteria for that rule (intersection semantics).

        Origin inheritance
        ------------------
        If a rule declares no origin behavior of its own, the nearest ancestor's
        origin is used. Rules with no resolved origin (no own or inherited) are
        omitted entirely — they have no genuine ROUTES_TO target.

        Path eligibility
        ----------------
        A rule is path-eligible (produces a Path node) iff pathCriteria is
        non-empty and there is no cloudlet conditional. The canonical path key
        is the sorted criteria joined with PATH_AND so the same set of criteria
        always maps to one Path node regardless of traversal order.

        Rules with zero path criteria (pure-negation, hostname-only,
        cloudlet-conditional, or catch-all) emit exactly one record with
        path=None — the Rule node is written but no Path node.
        """
        behaviors = rule.get("behaviors", [])

        ownPathCriteria, ownHostnameCriteria, conditionalOriginId = (
            self.extractRuleCriteria(rule)
        )

        combinedPathCriteria = (inheritedPathCriteria or []) + ownPathCriteria
        combinedHostnameCriteria = (
            inheritedHostnameCriteria or []
        ) + ownHostnameCriteria

        originHostname, originType = self.resolveOriginFromBehaviors(
            behaviors, inheritedOriginHostname, inheritedOriginType
        )

        securityBehaviors = self.extractSecurityBehaviors(behaviors)

        outboundPath, baseDirectory = self.resolveOutboundPathFromBehaviors(
            behaviors, inheritedOutboundPath, inheritedBaseDirectory
        )

        ruleName = rule.get("name", "default")

        isPathEligible = bool(combinedPathCriteria) and conditionalOriginId is None
        canonicalPath = (
            PATH_AND.join(sorted(combinedPathCriteria)) if isPathEligible else None
        )

        records = []

        # Only emit records if there is a genuine origin to route to
        if originHostname is not None:
            records.append(
                PropertyRuleRecord(
                    path=canonicalPath,
                    pathCriteria=combinedPathCriteria,
                    hostnameCriteria=combinedHostnameCriteria,
                    conditionalOriginId=conditionalOriginId,
                    originHostname=originHostname,
                    originType=originType,
                    outboundPath=outboundPath,
                    baseDirectory=baseDirectory,
                    ruleName=ruleName,
                    ruleDepth=depth,
                    criteriaMustSatisfy=rule.get("criteriaMustSatisfy", "all"),
                    securityBehaviors=securityBehaviors,
                    propertyId=propertyId,
                    propertyName=propertyName,
                    version=version,
                    deeplink=deeplink,
                )
            )

        for childRule in rule.get("children", []):
            records.extend(
                self.extractRuleRecords(
                    rule=childRule,
                    propertyId=propertyId,
                    propertyName=propertyName,
                    version=version,
                    deeplink=deeplink,
                    depth=depth + 1,
                    inheritedPathCriteria=combinedPathCriteria,
                    inheritedHostnameCriteria=combinedHostnameCriteria,
                    inheritedOriginHostname=originHostname,
                    inheritedOriginType=originType,
                    inheritedOutboundPath=outboundPath,
                    inheritedBaseDirectory=baseDirectory,
                )
            )

        return records

    def buildPropertyResponse(
        self, propertyId: str, hostnames: list
    ) -> AkamaiPropertyResponse | None:
        """Fetch full property details for one propertyId and return a typed response.

        Returns None if the API call fails (logged as exception).
        """
        propertyHostnames = [
            hostname for hostname in hostnames if hostname["propertyId"] == propertyId
        ]

        contractId = propertyHostnames[0]["contractId"]
        groupId = propertyHostnames[0]["groupId"]

        try:
            propertyResponse = self.getProperty(
                propertyId=propertyId,
                contractId=contractId,
                groupId=groupId,
            )
        except Exception as err:
            logger.exception("Failed to get property %s: %s", propertyId, err)
            return None

        propertyResponse["hostnames"] = propertyHostnames
        return AkamaiPropertyResponse.fromDict(propertyResponse)
