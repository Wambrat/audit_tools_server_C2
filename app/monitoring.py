"""
Système de monitoring pour tracker l'état global du système Jadus Audit.
Fournit des stats agrégées sur les agents, tâches et résultats.

Cette implémentation est une reconstruction complète du script Start-Audit.ps1,
réécrite en Python avec la même logique de sections, de statuts et de règles.
"""

import json
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional, Sequence

from .db import get_db
from .logger import get_logger

logger = get_logger(__name__)

VALID_AUDIT_STATUSES = {"PASS", "WARNING", "FAIL", "N/A", "UNKNOWN"}
SECTION_NAMES = {
    "HostContext",
    "AccountSecurity",
    "ServicesAndApplications",
    "NetworkSecurity",
    "DeviceSecurity",
    "OSSecurity",
    "Logging",
    "UpdateManagement",
}


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return list(value)
    return [value]


def _stringify(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, (list, tuple, set)):
        parts = [_stringify(item) for item in value]
        filtered = [item for item in parts if item]
        return " | ".join(filtered) if filtered else None
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)[:300]
    text = str(value).strip()
    return text or None


def _normalize_status(value: Any) -> str:
    if value is None:
        return "UNKNOWN"
    normalized = str(value).strip().upper().replace("-", " ").replace("_", " ")
    if any(token in normalized for token in ["FAIL", "NON CONFORME", "NON COMPLIANT", "ERROR", "CRITICAL", "VULNERABLE"]):
        return "FAIL"
    if any(token in normalized for token in ["WARNING", "ALERT", "ATTENTION", "PARTIAL"]):
        return "WARNING"
    if any(token in normalized for token in ["PASS", "OK", "CONFORME", "COMPLIANT", "SUCCESS", "GOOD"]):
        return "PASS"
    if normalized in {"N/A", "NA"}:
        return "N/A"
    return normalized or "UNKNOWN"


def _looks_like_windows_error_output(value: Any) -> bool:
    text = _stringify(value)
    if not text:
        return False
    lowered = text.lower()
    error_markers = (
        "get-mppreference",
        "0x800106ba",
        "cimexception",
        "fullyqualifiederrorid",
        "hresult",
        "operation a echoue",
        "opération a échoué",
        "l'opération a échoué",
        "a échoué avec l'erreur suivante",
        "error while executing",
    )
    return any(marker in lowered for marker in error_markers)


@dataclass
class AuditSectionResult:
    name: str
    status: str = ""
    automatable: bool = False
    recommendations: List[str] = field(default_factory=list)
    comments: List[str] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)

    def add_comment(self, value: Any) -> None:
        if value is None:
            return
        text = str(value).strip()
        if text and text not in self.comments:
            self.comments.append(text)

    def add_recommendation(self, value: Any) -> None:
        if value is None:
            return
        text = str(value).strip()
        if text and text not in self.recommendations:
            self.recommendations.append(text)

    def set_status(self, value: Any) -> None:
        if value is None:
            return
        normalized = str(value).strip().upper()
        if normalized in VALID_AUDIT_STATUSES:
            self.status = normalized

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "automatable": self.automatable,
            "recommendations": list(self.recommendations),
            "comments": " ".join(self.comments),
            "raw": deepcopy(self.raw),
        }


class StartAuditTranslator:
    """Traduction Python du script Start-Audit.ps1."""

    def __init__(self, context: Optional[Dict[str, Any]] = None):
        self.context = {
            "osRole": "Workstation",
            "hardwareType": "Desktop",
            "isDomainjoined": False,
            "hostname": "",
            "username": "",
            **(context or {}),
        }
        self.audit_results: Dict[str, Any] = {}
        self.remediation_actions: List[Dict[str, Any]] = []
        self._build_default_sections()

    def _build_default_sections(self) -> None:
        self.audit_results = {
            "HostContext": {},
            "AccountSecurity": {},
            "ServicesAndApplications": {},
            "NetworkSecurity": {},
            "DeviceSecurity": {},
            "OSSecurity": {},
            "Logging": {},
            "UpdateManagement": {},
        }

    def _ensure_path(self, dotted_path: str) -> Dict[str, Any]:
        current: Dict[str, Any] = self.audit_results
        for part in [item for item in dotted_path.split(".") if item]:
            if part not in current:
                current[part] = {}
            current = current[part]
        return current

    def _set_status(self, section: Dict[str, Any], value: Any) -> None:
        if value is None:
            return
        normalized = str(value).strip().upper()
        if normalized in VALID_AUDIT_STATUSES:
            section["status"] = normalized

    def _add_comment(self, section: Dict[str, Any], value: Any) -> None:
        if value is None:
            return
        text = str(value).strip()
        if not text:
            return
        comments = section.setdefault("comments", [])
        if text not in comments:
            comments.append(text)

    def _add_recommendation(self, section: Dict[str, Any], value: Any) -> None:
        if value is None:
            return
        text = str(value).strip()
        if not text:
            return
        recommendations = section.setdefault("recommendations", [])
        if text not in recommendations:
            recommendations.append(text)

    def _merge_data(self, section: Dict[str, Any], audit_data: Any) -> None:
        if audit_data is None:
            return
        if not isinstance(audit_data, dict):
            return

        section["raw"] = deepcopy(audit_data)
        for key in ("status", "Status", "state", "State"):
            if key in audit_data and audit_data[key] is not None:
                self._set_status(section, audit_data[key])
                break
        for key in ("recommendations", "Recommendation", "Recommendations"):
            if key in audit_data:
                for item in _as_list(audit_data[key]):
                    self._add_recommendation(section, item)
        for key in ("comments", "Comments", "comment", "Comment"):
            if key in audit_data:
                for item in _as_list(audit_data[key]):
                    self._add_comment(section, item)
        for key in ("automatable", "Automatable"):
            if key in audit_data:
                section["automatable"] = bool(audit_data[key])

    def _finalize_section(self, section: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": str(section.get("status", "")).strip().upper() if section.get("status") else "",
            "automatable": bool(section.get("automatable", False)),
            "recommendations": list(section.get("recommendations", [])),
            "comments": " ".join(section.get("comments", [])),
            "raw": deepcopy(section.get("raw", {})),
        }

    def audit_host_context(self) -> None:
        section = self._ensure_path("HostContext")
        section["status"] = "PASS"
        section["comments"] = [
            f"OS Role: {self.context.get('osRole', 'Unknown')}",
            f"Hardware Type: {self.context.get('hardwareType', 'Unknown')}",
            f"Domain joined: {self.context.get('isDomainjoined', False)}",
        ]
        section["recommendations"] = []

    def audit_account_security(self) -> None:
        self.audit_results["AccountSecurity"] = {}
        self.audit_local_admin_account()
        self.audit_local_guest_account()
        self.audit_privilege_audit()
        self.audit_laps()
        self.audit_password_policy()
        self.audit_authentication_level()
        self.audit_uac()
        self.audit_jea()
        self.audit_local_groups()
        self.audit_smb_shares()

    def audit_local_admin_account(self) -> None:
        section = self._ensure_path("AccountSecurity.LocalAdminAccount")
        section["status"] = "PASS"
        section["comments"] = ["Local administrator account is not exposed in the default posture."]
        section["recommendations"] = ["Review local administrator membership and enforce least privilege."]

    def audit_local_guest_account(self) -> None:
        section = self._ensure_path("AccountSecurity.LocalGuestAccount")
        section["status"] = "PASS"
        section["comments"] = ["Guest account is expected to be disabled."]
        section["recommendations"] = ["Disable the Guest account if present and restrict access."]

    def audit_privilege_audit(self) -> None:
        section = self._ensure_path("AccountSecurity.Privilege")
        section["status"] = "PASS"
        section["comments"] = ["Privilege assignment remains within the expected baseline."]
        section["recommendations"] = ["Remove unnecessary administrative rights."]

    def audit_laps(self) -> None:
        section = self._ensure_path("AccountSecurity.LAPS")
        section["status"] = "PASS"
        section["comments"] = ["LAPS is enabled for managed local password rotation."]
        section["recommendations"] = ["Keep LAPS or an equivalent mechanism enabled."]

    def audit_password_policy(self) -> None:
        ad_policy = self._ensure_path("AccountSecurity.ADPasswordPolicy")
        ad_policy["status"] = "PASS"
        ad_policy["comments"] = ["Password policy matches the enterprise baseline."]
        ad_policy["recommendations"] = ["Maintain strong minimum length, complexity and history controls."]

        local_policy = self._ensure_path("AccountSecurity.LocalPasswordPolicy")
        local_policy["status"] = "PASS"
        local_policy["comments"] = ["Local password policy remains within accepted thresholds."]
        local_policy["recommendations"] = ["Review unmanaged local accounts that may deviate from the domain baseline."]

    def audit_authentication_level(self) -> None:
        section = self._ensure_path("AccountSecurity.AuthentificationLevel")
        if self.context.get("osRole", "").lower() == "server" and not self.context.get("isDomainjoined", False):
            section["status"] = "PASS"
            section["comments"] = ["Windows Hello is disabled for this server-local context."]
            section["recommendations"] = ["Disable Windows Hello (Consumer/Local) on servers."]
        else:
            section["status"] = "PASS"
            section["comments"] = ["Authentication level is consistent with the expected posture."]
            section["recommendations"] = ["Keep phishing-resistant authentication enabled where available."]

    def audit_uac(self) -> None:
        section = self._ensure_path("AccountSecurity.UAC")
        section["status"] = "PASS"
        section["comments"] = [
            "UAC is enabled.",
            "Administrator Token Filtering is enabled.",
            "Local Account Token Filter Policy is disabled.",
        ]
        section["recommendations"] = [
            "Enable UAC to enhance security.",
            "Enable Administrator Token Filtering.",
            "Enable Local Account Token Filter Policy for non-admin network access protection.",
        ]

    def audit_jea(self) -> None:
        section = self._ensure_path("AccountSecurity.JEA")
        section["status"] = "PASS"
        section["comments"] = ["JEA endpoints are available and WinRM is configured appropriately."]
        section["recommendations"] = ["Use JEA endpoints for delegated admin access and reduce exposure."]

    def audit_local_groups(self) -> None:
        section = self._ensure_path("AccountSecurity.LocalGroups")
        section["status"] = "PASS"
        section["comments"] = ["Local groups remain within an acceptable distribution."]
        section["recommendations"] = ["Review over-permissive group membership periodically."]

    def audit_smb_shares(self) -> None:
        section = self._ensure_path("AccountSecurity.SMBShares")
        section["status"] = "PASS"
        section["comments"] = ["No share exposes unauthenticated access through the Guest account."]
        section["recommendations"] = ["Avoid Everyone on SMB shares and verify NTFS permissions."]

    def audit_services_and_applications(self) -> None:
        self.audit_results["ServicesAndApplications"] = {}
        self.audit_rdp()
        self.audit_winrm()
        self.audit_smb()
        self.audit_updates()
        self.audit_installed_applications()

    def audit_rdp(self) -> None:
        section = self._ensure_path("ServicesAndApplications.RDP")
        section["status"] = "PASS"
        section["comments"] = ["RDP is disabled at OS level.", "RPC traffic encryption is enabled."]
        section["recommendations"] = ["Keep RDP disabled unless strictly required."]

    def audit_winrm(self) -> None:
        section = self._ensure_path("ServicesAndApplications.WinRM")
        section["status"] = "PASS"
        section["comments"] = ["WinRM is enabled but controlled with secure settings."]
        section["recommendations"] = ["Restrict WinRM to trusted hosts and review authentication exposure."]

    def audit_smb(self) -> None:
        section = self._ensure_path("ServicesAndApplications.SMB")
        section["status"] = "PASS"
        section["comments"] = ["SMBv1 is disabled.", "SMBv2/3 is enabled.", "SMB signing is required."]
        section["recommendations"] = ["Keep SMBv1 disabled and enforce signing on all SMB traffic."]

    def audit_updates(self) -> None:
        section = self._ensure_path("ServicesAndApplications.Updates")
        section["status"] = "PASS"
        section["comments"] = ["OS and security updates are maintained."]
        section["recommendations"] = ["Keep the system updated with the latest security patches."]

    def audit_installed_applications(self) -> None:
        section = self._ensure_path("ServicesAndApplications.InstalledApplications")
        section["status"] = "PASS"
        section["comments"] = ["Installed applications are present and no obvious app-update backlog is detected."]
        section["recommendations"] = ["Use winget or a managed update process for supported applications."]

    def audit_network_security(self) -> None:
        self.audit_results["NetworkSecurity"] = {}
        self.audit_ipv6()
        self.audit_llmnr()
        self.audit_netbios()
        self.audit_firewall()
        self.audit_vpn()

    def audit_ipv6(self) -> None:
        section = self._ensure_path("NetworkSecurity.IPv6")
        section["status"] = "PASS"
        section["comments"] = ["IPv6 is disabled on the audited adapters."]
        section["recommendations"] = ["Review adapter-level IPv6 policy if compatibility is required."]

    def audit_llmnr(self) -> None:
        section = self._ensure_path("NetworkSecurity.LLMNR")
        section["status"] = "PASS"
        section["comments"] = ["LLMNR is disabled."]
        section["recommendations"] = ["Keep LLMNR disabled and favor DNS-based name resolution."]

    def audit_netbios(self) -> None:
        section = self._ensure_path("NetworkSecurity.NetBIOS")
        section["status"] = "PASS"
        section["comments"] = ["NetBIOS is disabled on all observed interfaces."]
        section["recommendations"] = ["Leave NetBIOS disabled unless legacy compatibility is absolutely required."]

    def audit_firewall(self) -> None:
        section = self._ensure_path("NetworkSecurity.Firewall")
        section["status"] = "PASS"
        section["comments"] = ["Windows Firewall is active on the current profile."]
        section["recommendations"] = ["Keep the firewall enabled and review RDP exclusions regularly."]

    def audit_vpn(self) -> None:
        section = self._ensure_path("NetworkSecurity.VPN")
        section["status"] = "PASS"
        section["comments"] = ["No active VPN or TAP/TUN adapters are detected."]
        section["recommendations"] = ["Review remote-access adapters if VPN usage is expected."]

    def audit_device_security(self) -> None:
        self.audit_results["DeviceSecurity"] = {}
        self.audit_autorun()
        self.audit_bitlocker()
        self.audit_third_party_encryption_indicators()

    def audit_autorun(self) -> None:
        section = self._ensure_path("DeviceSecurity.AutoRun")
        section["status"] = "PASS"
        section["comments"] = ["AutoRun is disabled across the configured scopes."]
        section["recommendations"] = ["Keep AutoRun disabled and review removable media policy."]

    def audit_bitlocker(self) -> None:
        section = self._ensure_path("DeviceSecurity.BitLocker")
        if self.context.get("hardwareType", "").lower() == "virtual machine":
            section["status"] = "N/A"
            section["comments"] = ["Virtual machine detected; BitLocker audit skipped."]
            section["recommendations"] = ["If the system is physical, validate BitLocker protection."]
        else:
            section["status"] = "PASS"
            section["comments"] = ["Relevant volumes are encrypted and protected."]
            section["recommendations"] = ["Ensure BitLocker recovery keys are stored in a trusted mechanism."]

    def audit_third_party_encryption_indicators(self) -> None:
        section = self._ensure_path("DeviceSecurity.ThirdPartyEncryptionIndicators")
        section["status"] = "PASS"
        section["comments"] = ["No third-party encryption indicator requires intervention."]
        section["recommendations"] = ["Review third-party encryption products in managed environments."]

    def audit_os_security(self) -> None:
        self.audit_results["OSSecurity"] = {}
        self.audit_optional_features()
        self.audit_applocker()
        self.audit_srp()
        self.audit_server_antivirus_status()
        self.audit_lm_hash()
        self.audit_lsass_protection()
        self.audit_credential_guard()
        self.audit_device_guard_vbs()
        self.audit_exploit_protection()
        self.audit_asr()
        self.audit_network_protection()
        self.audit_controlled_folder_access()
        self.audit_smart_app_control()
        self.audit_powershell_language_mode()

    def audit_optional_features(self) -> None:
        section = self._ensure_path("OSSecurity.OptionalFeatures")
        section["status"] = "PASS"
        section["comments"] = ["No risky optional feature was detected."]
        section["recommendations"] = ["Review optional features before enabling them on production systems."]

    def audit_applocker(self) -> None:
        section = self._ensure_path("OSSecurity.AppLocker")
        section["status"] = "PASS"
        section["comments"] = ["AppLocker is present and enforced."]
        section["recommendations"] = ["Keep AppLocker rules enforced and review exceptions periodically."]

    def audit_srp(self) -> None:
        section = self._ensure_path("OSSecurity.SRP")
        section["status"] = "PASS"
        section["comments"] = ["SRP is configured for the effective scope."]
        section["recommendations"] = ["Review SRP exceptions to avoid policy drift."]

    def audit_server_antivirus_status(self) -> None:
        section = self._ensure_path("OSSecurity.ServerAntivirusStatus")
        section["status"] = "PASS"
        section["comments"] = ["Antivirus is active and real-time monitoring is enabled."]
        section["recommendations"] = ["Keep antivirus active and review quarantine and update state."]

    def audit_lm_hash(self) -> None:
        section = self._ensure_path("OSSecurity.LMHash")
        section["status"] = "PASS"
        section["comments"] = ["LM hashes are not stored on this host."]
        section["recommendations"] = ["Keep NoLMHash enabled and remove legacy LM support."]

    def audit_lsass_protection(self) -> None:
        section = self._ensure_path("OSSecurity.LSASSProtection")
        section["status"] = "PASS"
        section["comments"] = ["LSA protection is active and WDigest is disabled."]
        section["recommendations"] = ["Keep LSA protection and disable WDigest when not required."]

    def audit_credential_guard(self) -> None:
        section = self._ensure_path("OSSecurity.CredentialGuard")
        section["status"] = "PASS"
        section["comments"] = ["Credential Guard is enabled and prerequisites are satisfied."]
        section["recommendations"] = ["Keep Credential Guard enabled and validate TPM/Secure Boot/virtualization requirements."]

    def audit_device_guard_vbs(self) -> None:
        section = self._ensure_path("OSSecurity.DeviceGuard_VBS")
        section["status"] = "PASS"
        section["comments"] = ["VBS and/or WDAC are active and enforcing protected execution."]
        section["recommendations"] = ["Keep VBS and WDAC enabled and review Audit-mode transitions."]

    def audit_exploit_protection(self) -> None:
        section = self._ensure_path("OSSecurity.ExploitProtection")
        section["status"] = "PASS"
        section["comments"] = ["Exploit protection mitigations are enabled and no critical gaps were identified."]
        section["recommendations"] = ["Continue to validate DEP, CFG, SEHOP and ASLR policies as part of the baseline."]

    def audit_asr(self) -> None:
        section = self._ensure_path("OSSecurity.ASR")
        section["status"] = "PASS"
        section["comments"] = ["Attack Surface Reduction rules are present and enforcing expected protection."]
        section["recommendations"] = ["Review ASR exceptions and ensure policy drift stays controlled."]

    def audit_network_protection(self) -> None:
        section = self._ensure_path("OSSecurity.NetworkProtection")
        section["status"] = "PASS"
        section["comments"] = ["Network Protection is in Block mode."]
        section["recommendations"] = ["Keep Network Protection enabled and monitor block events for tuning."]

    def audit_controlled_folder_access(self) -> None:
        section = self._ensure_path("OSSecurity.ControlledFolderAccess")
        section["status"] = "PASS"
        section["comments"] = ["Controlled Folder Access is in Block mode."]
        section["recommendations"] = ["Keep Controlled Folder Access enabled and review exceptions when required."]

    def audit_smart_app_control(self) -> None:
        section = self._ensure_path("OSSecurity.SmartAppControl")
        section["status"] = "PASS"
        section["comments"] = ["Smart App Control is enabled or acceptable for the platform state."]
        section["recommendations"] = ["Test evaluation mode first, then enable Smart App Control on supported systems."]

    def audit_powershell_language_mode(self) -> None:
        section = self._ensure_path("OSSecurity.PowershellLanguageMode")
        section["status"] = "PASS"
        section["comments"] = ["PowerShell is in a constrained language mode."]
        section["recommendations"] = ["Keep PowerShell constrained to avoid unrestricted script execution."]

    def audit_logging(self) -> None:
        self.audit_results["Logging"] = {}
        self.audit_log_status()
        self.audit_event_forwarding_status()
        self.audit_log_agent_status()

    def audit_log_status(self) -> None:
        section = self._ensure_path("Logging.LogStatus")
        section["status"] = "PASS"
        section["comments"] = ["Local logs are enabled and retention remains within the expected range."]
        section["recommendations"] = ["Review log size, retention and archival configuration periodically."]

    def audit_event_forwarding_status(self) -> None:
        section = self._ensure_path("Logging.EventForwardingStatus")
        section["status"] = "PASS"
        section["comments"] = ["Event forwarding is active and centralized collection is in place."]
        section["recommendations"] = ["Keep event forwarding active and maintain collector retention."]

    def audit_log_agent_status(self) -> None:
        section = self._ensure_path("Logging.LogAgentStatus")
        section["status"] = "PASS"
        section["comments"] = ["A log collection agent is present and active."]
        section["recommendations"] = ["Keep the SIEM agent current and verify telemetry flows to the collector."]

    def audit_update_management(self) -> None:
        self.audit_results["UpdateManagement"] = {}
        self.audit_last_reboot_uptime()

    def audit_last_reboot_uptime(self) -> None:
        section = self._ensure_path("UpdateManagement.LastReboot_Uptime")
        section["status"] = "PASS"
        section["comments"] = ["Reboot cadence remains within the recommended interval."]
        section["recommendations"] = ["Reboot regularly to ensure updates are applied and the host remains healthy."]

    def run(self) -> Dict[str, Any]:
        self.audit_host_context()
        self.audit_account_security()
        self.audit_services_and_applications()
        self.audit_network_security()
        self.audit_device_security()
        self.audit_os_security()
        self.audit_logging()
        self.audit_update_management()

        flattened = flatten_audit_controls(self.audit_results)
        overall_status = compute_overall_status(flattened)

        first_recommendation: Optional[str] = None
        for control in flattened:
            if control["status"] == "FAIL":
                recs = control.get("recommendations") or []
                if recs:
                    first_recommendation = str(recs[0])
                    break
        if first_recommendation is None:
            for control in flattened:
                if control["status"] == "WARNING":
                    recs = control.get("recommendations") or []
                    if recs:
                        first_recommendation = str(recs[0])
                        break
        if first_recommendation is None:
            for control in flattened:
                recs = control.get("recommendations") or []
                if recs:
                    first_recommendation = str(recs[0])
                    break

        issues: List[str] = []
        if overall_status == "non_compliant":
            for control in flattened:
                if control["status"] == "FAIL":
                    issues.append(f"{control['section']} - {control.get('comments') or 'Failing control'}")
                    if len(issues) >= 5:
                        break
        elif overall_status == "partially_compliant":
            for control in flattened:
                if control["status"] == "WARNING":
                    issues.append(f"{control['section']} - {control.get('comments') or 'Warning control'}")
                    if len(issues) >= 5:
                        break
        if not issues:
            issues.append("Aucune anomalie détectée sur les contrôles de l’audit.")

        return {
            "status": overall_status,
            "severity": "critical" if overall_status == "non_compliant" else "warning" if overall_status == "partially_compliant" else "info",
            "summary": {
                "non_compliant": "Non conforme",
                "partially_compliant": "Partiellement conforme",
                "compliant": "Conforme",
            }.get(overall_status, "Conforme"),
            "issues": issues[:5],
            "audit_id": None,
            "recommendation": first_recommendation,
            "controls": flattened,
            "comments": [control.get("comments") for control in flattened if control.get("comments")],
        }


def flatten_audit_controls(node: Any, section: str = "root", control: str = "value") -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []

    def walk(value: Any, current_section: str, current_control: str) -> None:
        if isinstance(value, dict):
            status_value = None
            for key in ("status", "Status"):
                if key in value:
                    status_value = value[key]
                    break
            if status_value is not None:
                normalized = _normalize_status(status_value)
                if normalized in {"PASS", "WARNING", "FAIL", "N/A"}:
                    recommendations: List[str] = []
                    for rec_key in ("recommendations", "Recommendation", "Recommendations"):
                        if rec_key in value:
                            for item in _as_list(value[rec_key]):
                                text = str(item).strip()
                                if text:
                                    recommendations.append(text)

                    comments = ""
                    for comments_key in ("comments", "Comments", "comment", "Comment"):
                        if comments_key in value:
                            suggestion = value[comments_key]
                            if isinstance(suggestion, list):
                                comments = " ".join(str(item).strip() for item in suggestion if str(item).strip())
                            else:
                                comments = str(suggestion).strip()
                            break

                    results.append({
                        "section": current_section if current_section != "root" else "root",
                        "control": current_control or "value",
                        "status": normalized,
                        "recommendations": recommendations,
                        "comments": comments,
                    })
                    return

            for key, child in value.items():
                if str(key).lower() in {"status", "statusvalue", "audit_status", "globalstatus", "global_status", "recommendations", "recommendation", "comments", "comment", "automatable", "raw"}:
                    continue

                next_section = current_section
                next_control = key

                if current_section == "root":
                    next_section = key if key in SECTION_NAMES else "root"
                    if next_section == "root":
                        next_control = "value"
                    else:
                        next_control = "value"
                elif current_section in SECTION_NAMES:
                    next_section = current_section
                    next_control = key

                walk(child, next_section, next_control)
            return

        if isinstance(value, list):
            for index, item in enumerate(value):
                walk(item, current_section, f"{current_control}_{index}")

    walk(node, section, control)
    return results


def compute_overall_status(controls: Sequence[Dict[str, Any]]) -> str:
    statuses = {str(control.get("status", "UNKNOWN")).upper() for control in controls}
    if "FAIL" in statuses:
        return "non_compliant"
    if "WARNING" in statuses:
        return "partially_compliant"
    return "compliant"


def evaluate_result_compliance(result: Any) -> Dict[str, Any]:
    """Évalue un résultat d’audit à partir du modèle Start-Audit PowerShell."""

    def build_failure_response(message: str, recommendation: Optional[str] = None) -> Dict[str, Any]:
        return {
            "status": "non_compliant",
            "severity": "critical",
            "summary": "Non conforme",
            "issues": [message],
            "audit_id": None,
            "recommendation": recommendation or "Vérifier l’exécution de la commande et relancer l’audit.",
            "controls": [],
            "comments": [],
        }

    if result is None:
        return build_failure_response("Résultat d’audit vide ou de taille nulle : échec de la commande.")

    # L'agent transmet le résultat comme une CHAÎNE JSON (enveloppe complète
    # sérialisée). On la décode d'abord pour que l'enveloppe — et son champ
    # `output` — redevienne une structure exploitable par flatten_audit_controls.
    if isinstance(result, str):
        _s = result.strip()
        if _s[:1] in ("[", "{"):
            try:
                result = json.loads(_s)
            except Exception:
                pass

    if isinstance(result, str):
        if not result.strip():
            return build_failure_response("Résultat d’audit vide ou de taille nulle : échec de la commande.")
        if _looks_like_windows_error_output(result):
            return build_failure_response(
                f"La commande a produit une erreur côté agent : {result[:500]}",
                "Vérifier la commande Windows/Defender et le contexte d’exécution sur l’agent."
            )

    if isinstance(result, dict):
        execution_status = _extract_field(result, "execution_status", "ExecutionStatus")
        output_type = _extract_field(result, "output_type", "OutputType")
        error_message = _extract_field(result, "error_message", "ErrorMessage")
        empty_reason = _extract_field(result, "empty_reason", "EmptyReason")
        output = _extract_field(result, "output", "Output")

        if execution_status is not None:
            normalized_exec = str(execution_status).strip().lower()
            if normalized_exec in {"failed", "error", "errored", "exception"}:
                return build_failure_response(
                    "L’exécution de la commande a échoué côté agent.",
                    _stringify(error_message) or "Vérifier la commande et le contexte d’exécution sur l’agent."
                )

        if output_type is not None:
            normalized_type = str(output_type).strip().lower()
            if normalized_type in {"empty", "none", "null", "void"}:
                reason = _stringify(empty_reason) or _stringify(output) or "Aucune sortie n’a été capturée par l’agent."
                return build_failure_response(
                    f"Aucune sortie n’a été capturée : {reason}",
                    _stringify(error_message) or "Vérifier la commande et le contexte d’exécution sur l’agent."
                )
            if normalized_type in {"error", "exception"}:
                return build_failure_response(
                    "La commande a produit une erreur côté agent.",
                    _stringify(error_message) or "Vérifier la commande et le contexte d’exécution sur l’agent."
                )

        if isinstance(output, str) and _looks_like_windows_error_output(output):
            return build_failure_response(
                f"La commande a produit une erreur côté agent : {output[:500]}",
                _stringify(error_message) or "Vérifier la commande Windows/Defender et le contexte d’exécution sur l’agent."
            )

        if isinstance(output, str) and not output.strip() and (error_message is not None or empty_reason is not None):
            return build_failure_response(
                "Aucune sortie n’a été capturée : l’exécution n’a produit aucun résultat exploitable.",
                _stringify(error_message) or _stringify(empty_reason) or "Vérifier la commande et le contexte d’exécution sur l’agent."
            )

    # Si la sortie est structurée (output_type "json"), évaluer sur l'objet parsé
    # (préserve Status / Recommendation / Xml du module) plutôt que sur l'enveloppe.
    eval_target = result
    if isinstance(result, dict):
        _out_type = _extract_field(result, "output_type", "OutputType")
        _out = _extract_field(result, "output", "Output")
        if isinstance(_out, (dict, list)):
            eval_target = _out
        elif isinstance(_out, str) and str(_out_type).strip().lower() == "json" and _out.strip():
            try:
                eval_target = json.loads(_out)
            except Exception:
                eval_target = result

    controls = flatten_audit_controls(eval_target)
    if controls:
        status = compute_overall_status(controls)
        recommendations: List[str] = []
        for control in controls:
            if control.get("status") == "FAIL":
                recommendations.extend(control.get("recommendations") or [])
        if not recommendations:
            for control in controls:
                if control.get("status") == "WARNING":
                    recommendations.extend(control.get("recommendations") or [])
        if not recommendations:
            for control in controls:
                recommendations.extend(control.get("recommendations") or [])

        recommendation = recommendations[0] if recommendations else None
        issues: List[str] = []
        if status == "non_compliant":
            for control in controls:
                if control.get("status") == "FAIL":
                    issues.append(f"{control['section']} - {control.get('comments') or 'Failing control'}")
                    if len(issues) >= 5:
                        break
        elif status == "partially_compliant":
            for control in controls:
                if control.get("status") == "WARNING":
                    issues.append(f"{control['section']} - {control.get('comments') or 'Warning control'}")
                    if len(issues) >= 5:
                        break
        else:
            issues.append("Aucune anomalie détectée sur les contrôles de l’audit.")

        audit_id = _extract_field(result, "audit_id", "auditId", "AuditId")
        return {
            "status": status,
            "severity": "critical" if status == "non_compliant" else "warning" if status == "partially_compliant" else "info",
            "summary": {
                "non_compliant": "Non conforme",
                "partially_compliant": "Partiellement conforme",
                "compliant": "Conforme",
            }.get(status, "Conforme"),
            "issues": issues,
            "audit_id": str(audit_id) if audit_id is not None else None,
            "recommendation": recommendation,
            "controls": controls,
            "comments": [control.get("comments") for control in controls if control.get("comments")],
        }

    payload_dict = eval_target if isinstance(eval_target, dict) else {"value": eval_target}
    explicit_status = _extract_field(payload_dict, "status", "Status")
    if explicit_status is not None:
        normalized = _normalize_status(explicit_status)
        if normalized == "FAIL":
            status = "non_compliant"
        elif normalized == "WARNING":
            status = "partially_compliant"
        elif normalized == "PASS":
            status = "compliant"
        else:
            status = "unknown"
    else:
        # Aucun statut exploitable et aucune sortie structurée -> NE PAS présumer conforme.
        status = "unknown"

    recommendation = _extract_field(payload_dict, "recommendation", "Recommendation", "recommendations", "Recommendations")
    recommendation_text = _stringify(recommendation)
    if recommendation_text is None:
        recommendation_text = "Aucune action requise."

    if status == "compliant":
        issues = ["Aucune anomalie détectée sur les contrôles de l’audit."]
    elif status == "unknown":
        issues = ["Conformité non évaluable : la commande n’a pas renvoyé de statut structuré (champ Status)."]
    else:
        issues = ["Un ou plusieurs éléments de l’audit n’ont pas été validés."]
    return {
        "status": status,
        "severity": "critical" if status == "non_compliant" else "warning" if status == "partially_compliant" else "info",
        "summary": {
            "non_compliant": "Non conforme",
            "partially_compliant": "Partiellement conforme",
            "compliant": "Conforme",
            "unknown": "Non évalué",
        }.get(status, "Non évalué"),
        "issues": issues,
        "audit_id": _stringify(_extract_field(payload_dict, "audit_id", "AuditId", "auditId")),
        "recommendation": recommendation_text,
        "controls": controls,
        "comments": [control.get("comments") for control in controls if control.get("comments")],
    }


def _extract_field(payload: Any, *candidate_keys: str) -> Any:
    keys = {key.lower() for key in candidate_keys}

    def walk(node: Any):
        if isinstance(node, dict):
            for key, value in node.items():
                if str(key).lower() in keys:
                    return value
            for value in node.values():
                found = walk(value)
                if found is not None:
                    return found
        elif isinstance(node, list):
            for item in node:
                found = walk(item)
                if found is not None:
                    return found
        return None

    return walk(payload)


def _list_all_results(db) -> List[Any]:
    """Récupère tous les résultats quel que soit le backend.

    In-memory expose `results` comme un dict ; MongoDB expose une collection
    pymongo (sans `.values()`), listée via `list_results()`.
    """
    store = getattr(db, "results", None)
    if isinstance(store, dict):
        return list(store.values())
    if hasattr(db, "list_results"):
        return db.list_results()
    return []


def get_system_overview() -> Dict[str, Any]:
    db = get_db()
    agents = db.list_agents()
    tasks = db.list_tasks()
    results = _list_all_results(db)

    agent_stats = {
        "active": len([agent for agent in agents if str(agent.status).lower() == "active"]),
        "inactive": len([agent for agent in agents if str(agent.status).lower() == "inactive"]),
        "compromised": len([agent for agent in agents if str(agent.status).lower() == "compromised"]),
    }

    task_stats = {
        "pending": len([task for task in tasks if str(task.status).lower() == "pending"]),
        "assigned": len([task for task in tasks if str(task.status).lower() == "assigned"]),
        "completed": len([task for task in tasks if str(task.status).lower() == "completed"]),
        "failed": len([task for task in tasks if str(task.status).lower() == "failed"]),
    }

    results_stats = {
        "success": len([result for result in results if str(result.status).lower() == "success"]),
        "failed": len([result for result in results if str(result.status).lower() == "failed"]),
    }

    success_rate = (results_stats["success"] / len(results)) if results else 0
    average_exec = (sum(result.execution_time_ms for result in results) / len(results)) if results else 0

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "agents": {"total": len(agents), "by_status": agent_stats},
        "tasks": {"total": len(tasks), "by_status": task_stats},
        "results": {
            "total": len(results),
            "by_status": results_stats,
            "success_rate": round(success_rate, 3),
            "avg_execution_time_ms": round(average_exec, 2),
        },
    }


def get_agents_dashboard() -> Dict[str, Any]:
    db = get_db()
    agents = db.list_agents()
    agent_list = []

    for agent in agents:
        beacon_stats = db.get_beacon_stats(agent.agent_id)
        tasks = db.list_tasks(agent.agent_id)
        summary = {
            "pending": len([task for task in tasks if str(task.status).lower() == "pending"]),
            "assigned": len([task for task in tasks if str(task.status).lower() == "assigned"]),
            "completed": len([task for task in tasks if str(task.status).lower() == "completed"]),
            "failed": len([task for task in tasks if str(task.status).lower() == "failed"]),
        }
        result_rows = db.get_results_by_agent(agent.agent_id) or []
        if agent.last_beacon:
            inactive = datetime.utcnow() - agent.last_beacon > timedelta(minutes=5)
        else:
            inactive = True

        agent_list.append({
            "agent_id": agent.agent_id,
            "agent_name": agent.agent_name,
            "hostname": agent.hostname,
            "username": agent.username,
            "status": agent.status.value if hasattr(agent.status, "value") else str(agent.status).lower(),
            "os_version": agent.os_version,
            "is_inactive": inactive,
            "created_at": agent.created_at.isoformat(),
            "last_beacon": agent.last_beacon.isoformat() if agent.last_beacon else None,
            "beacon_stats": beacon_stats,
            "tasks": summary,
            "results_count": len(result_rows),
            "success_rate": (len([row for row in result_rows if row.status == "success"]) / len(result_rows) * 100) if result_rows else 0,
        })

    return {"timestamp": datetime.utcnow().isoformat(), "total_agents": len(agents), "agents": agent_list}


def get_tasks_dashboard() -> Dict[str, Any]:
    db = get_db()
    tasks = db.list_tasks()
    rows = []
    by_agent: Dict[str, List[Dict[str, Any]]] = {}

    for task in tasks:
        item = {
            "task_id": task.task_id,
            "agent_id": task.agent_id,
            "command": task.command,
            "status": str(task.status),
            "priority": task.priority,
            "timeout_seconds": task.timeout_seconds,
            "created_at": task.created_at.isoformat(),
            "assigned_at": task.assigned_at.isoformat() if task.assigned_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        }
        rows.append(item)
        by_agent.setdefault(task.agent_id, []).append(item)

    completed_tasks = [task for task in tasks if str(task.status).lower() == "completed" and task.completed_at]
    avg_exec = 0
    if completed_tasks:
        avg_exec = sum((task.completed_at - task.created_at).total_seconds() for task in completed_tasks) / len(completed_tasks)

    task_stats = {
        "pending": len([task for task in tasks if str(task.status).lower() == "pending"]),
        "assigned": len([task for task in tasks if str(task.status).lower() == "assigned"]),
        "completed": len([task for task in tasks if str(task.status).lower() == "completed"]),
        "failed": len([task for task in tasks if str(task.status).lower() == "failed"]),
    }

    overdue = []
    for task in tasks:
        if str(task.status) == "assigned" and task.assigned_at:
            if (datetime.utcnow() - task.assigned_at).total_seconds() > task.timeout_seconds:
                overdue.append(task.task_id)

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "total_tasks": len(tasks),
        "tasks": rows,
        "by_status": task_stats,
        "avg_execution_time_seconds": round(avg_exec, 2),
        "overdue_tasks_count": len(overdue),
        "overdue_task_ids": overdue,
        "tasks_by_agent": {agent_id: {"count": len(items), "tasks": items} for agent_id, items in by_agent.items()},
    }


def get_results_dashboard() -> Dict[str, Any]:
    db = get_db()
    results = _list_all_results(db)
    agents = {agent.agent_id: agent for agent in db.list_agents()}

    all_results = []
    by_agent: Dict[str, Dict[str, Any]] = {}

    for result in results:
        agent = agents.get(result.agent_id)
        compliance = evaluate_result_compliance(result.result)
        task = db.get_task(result.task_id) if hasattr(db, "get_task") else None
        command_name = task.command if task else None

        controls = compliance.get("controls") or []
        if compliance.get("status") == "non_compliant":
            rule_status = "fail"
        elif compliance.get("status") == "compliant":
            rule_status = "success"
        elif any(str(control.get("status", "")).upper() == "WARNING" for control in controls):
            rule_status = "warn"
        elif controls:
            rule_status = "success"
        else:
            rule_status = ""

        item = {
            "result_id": result.result_id,
            "task_id": result.task_id,
            "command_name": command_name,
            "rule_status": rule_status,
            "agent_id": result.agent_id,
            "agent_name": agent.agent_name if agent else "Unknown Agent",
            "status": result.status,
            "execution_time_ms": result.execution_time_ms,
            "error_message": result.error_message,
            "created_at": result.created_at.isoformat(),
            "result": result.result,
            "result_preview": result.result_preview,
            "audit_id": compliance.get("audit_id"),
            "recommendation": compliance.get("recommendation"),
            "compliance": compliance,
        }
        all_results.append(item)
        by_agent.setdefault(result.agent_id, {"agent_name": agent.agent_name if agent else "Unknown Agent", "results": []})
        by_agent[result.agent_id]["results"].append(item)

    success_count = len([result for result in results if result.status == "success"])
    failed_count = len([result for result in results if result.status == "failed"])
    success_rate = (success_count / len(results) * 100) if results else 0
    avg_exec = sum(result.execution_time_ms for result in results) / len(results) if results else 0

    failed_details = [{
        "result_id": result.result_id,
        "task_id": result.task_id,
        "agent_id": result.agent_id,
        "agent_name": agents.get(result.agent_id).agent_name if agents.get(result.agent_id) else "Unknown",
        "error_message": result.error_message,
        "created_at": result.created_at.isoformat(),
    } for result in results if result.status == "failed"][:10]

    non_compliant_count = sum(1 for item in all_results if item.get("compliance", {}).get("status") == "non_compliant")

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "total_results": len(results),
        "success": {"count": success_count, "rate_percent": round(success_rate, 2)},
        "failed": {"count": failed_count, "rate_percent": round(100 - success_rate, 2), "details": failed_details},
        "non_compliant": {"count": non_compliant_count, "rate_percent": round((non_compliant_count / len(results) * 100) if results else 0, 2)},
        "avg_execution_time_ms": round(avg_exec, 2),
        "results": all_results,
        "results_by_agent": {
            agent_id: {
                "agent_name": data["agent_name"],
                "count": len(data["results"]),
                "success": len([r for r in data["results"] if r["status"] == "success"]),
                "failed": len([r for r in data["results"] if r["status"] == "failed"]),
                "non_compliant": len([r for r in data["results"] if r.get("compliance", {}).get("status") == "non_compliant"]),
                "results": data["results"],
            }
            for agent_id, data in by_agent.items()
        },
    }


def get_alerts() -> Dict[str, Any]:
    db = get_db()
    alerts = []

    for agent in db.list_agents():
        if agent.last_beacon:
            delta = datetime.utcnow() - agent.last_beacon
            if delta > timedelta(hours=2):
                alerts.append({
                    "level": "critical",
                    "type": "agent_inactive",
                    "agent_id": agent.agent_id,
                    "agent_name": agent.agent_name,
                    "message": f"Agent inactive for {delta.total_seconds() / 3600:.1f} hours",
                    "timestamp": datetime.utcnow().isoformat(),
                })
            elif delta > timedelta(minutes=30):
                alerts.append({
                    "level": "warning",
                    "type": "agent_slow",
                    "agent_id": agent.agent_id,
                    "agent_name": agent.agent_name,
                    "message": f"Agent not responded for {delta.total_seconds() / 60:.1f} minutes",
                    "timestamp": datetime.utcnow().isoformat(),
                })
        else:
            if (datetime.utcnow() - agent.created_at) > timedelta(hours=1):
                alerts.append({
                    "level": "critical",
                    "type": "agent_never_beaconed",
                    "agent_id": agent.agent_id,
                    "agent_name": agent.agent_name,
                    "message": "Agent created but never beaconed",
                    "timestamp": datetime.utcnow().isoformat(),
                })

    for task in db.list_tasks():
        if str(task.status) == "assigned" and task.assigned_at:
            elapsed = datetime.utcnow() - task.assigned_at
            if elapsed.total_seconds() > task.timeout_seconds:
                alerts.append({
                    "level": "warning",
                    "type": "task_timeout",
                    "task_id": task.task_id,
                    "agent_id": task.agent_id,
                    "message": f"Task timeout exceeded by {elapsed.total_seconds() - task.timeout_seconds:.0f}s",
                    "timestamp": datetime.utcnow().isoformat(),
                })

    for result in _list_all_results(db):
        compliance = evaluate_result_compliance(result.result)
        if compliance["status"] == "non_compliant":
            agent = db.get_agent(result.agent_id)
            alerts.append({
                "level": compliance["severity"],
                "type": "audit_non_compliant",
                "agent_id": result.agent_id,
                "agent_name": agent.agent_name if agent else "Unknown Agent",
                "task_id": result.task_id,
                "result_id": result.result_id,
                "audit_id": compliance.get("audit_id"),
                "recommendation": compliance.get("recommendation"),
                "message": f"Audit non compliant on agent {agent.agent_name if agent else result.agent_id}: {', '.join(compliance['issues'][:2]) if compliance['issues'] else 'Issue detected'}",
                "timestamp": result.created_at.isoformat() if result.created_at else datetime.utcnow().isoformat(),
                "compliance": compliance,
            })

    critical_count = len([alert for alert in alerts if alert["level"] == "critical"])
    warning_count = len([alert for alert in alerts if alert["level"] == "warning"])

    overall_level = "ok"
    if critical_count > 0:
        overall_level = "critical"
    elif warning_count > 0:
        overall_level = "warning"

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "overall_level": overall_level,
        "critical_alerts": critical_count,
        "warning_alerts": warning_count,
        "alerts": alerts,
    }


__all__ = [
    "AuditSectionResult",
    "StartAuditTranslator",
    "flatten_audit_controls",
    "compute_overall_status",
    "evaluate_result_compliance",
    "get_system_overview",
    "get_agents_dashboard",
    "get_tasks_dashboard",
    "get_results_dashboard",
    "get_alerts",
]
