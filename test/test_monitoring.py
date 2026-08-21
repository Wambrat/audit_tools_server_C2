from fastapi.testclient import TestClient

from main import app
from app.db import get_db
from app.monitoring import evaluate_result_compliance

client = TestClient(app)


def test_result_submission_accepts_dict_payload():
    db = get_db()
    agent = db.create_agent(
        agent_name="Demo Agent",
        os_version="Windows 11",
        hostname="DEMO-HOST",
        username="demo-user",
    )
    task = db.create_task(
        agent_id=agent.agent_id,
        command="Get-LocalUserAudit",
        parameters={"mode": "demo"},
        priority=1,
    )

    response = client.post(
        "/api/results",
        json={
            "agent_id": agent.agent_id,
            "api_key": agent.api_key,
            "task_id": task.task_id,
            "status": "failed",
            "result": {
                "AuditId": "demo-audit-01",
                "Status": "FAIL",
                "Recommendation": "Renommer le compte administrateur local.",
            },
            "execution_time_ms": 1450,
            "error_message": None,
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["acknowledged"] is True
    assert any(r.agent_id == agent.agent_id for r in db.results.values())


def test_compliance_uses_business_status_and_recommendation():
    payload = {
        "AuditId": "audit-42",
        "Status": "FAIL",
        "Recommendation": "Appliquer le correctif de sécurité sur le mot de passe."
    }

    result = evaluate_result_compliance(payload)

    assert result["status"] == "non_compliant"
    assert result["audit_id"] == "audit-42"
    assert result["recommendation"] == "Appliquer le correctif de sécurité sur le mot de passe."


def test_compliance_accepts_pass_status():
    payload = {
        "Status": "PASS",
        "Recommendation": "Aucune action requise."
    }

    result = evaluate_result_compliance(payload)

    assert result["status"] == "compliant"
    assert result["recommendation"] == "Aucune action requise."


def test_compliance_maps_start_audit_controls():
    payload = {
        "HostContext": {"OSRole": "Workstation"},
        "AccountSecurity": {
            "LocalAdminAccount": {
                "status": "FAIL",
                "recommendations": ["Désactiver le compte administrateur local."],
                "comments": "Compte administrateur local actif."
            },
            "LocalGuestAccount": {
                "status": "PASS",
                "recommendations": ["Aucune action requise."],
                "comments": "Compte invité désactivé."
            }
        }
    }

    result = evaluate_result_compliance(payload)

    assert result["status"] == "non_compliant"
    assert result["recommendation"] == "Désactiver le compte administrateur local."
    assert any(control["section"] == "AccountSecurity" and control["control"] == "LocalAdminAccount" for control in result["controls"])
    assert result["controls"][0]["status"] in {"FAIL", "PASS", "WARNING"}


def test_compliance_maps_warning_to_partially_compliant():
    payload = {
        "AccountSecurity": {
            "LAPS": {
                "status": "WARNING",
                "recommendations": ["Vérifier la configuration LAPS pour éviter les méthodes obsolètes."],
                "comments": "LAPS utilise une méthode legacy partiellement compatible."
            }
        }
    }

    result = evaluate_result_compliance(payload)

    assert result["status"] == "partially_compliant"
    assert result["summary"] == "Partiellement conforme"
    assert result["recommendation"] == "Vérifier la configuration LAPS pour éviter les méthodes obsolètes."


def test_compliance_handles_function_level_payloads():
    payload = {
        "Get-FirewallAudit": {
            "status": "FAIL",
            "recommendations": ["Ouvrir le pare-feu sur les ports nécessaires."],
            "comments": "Le pare-feu laisse passer le trafic non désiré."
        }
    }

    result = evaluate_result_compliance(payload)

    assert result["status"] == "non_compliant"
    assert result["recommendation"] == "Ouvrir le pare-feu sur les ports nécessaires."
    assert any(control["control"] == "value" for control in result["controls"])


def test_compliance_marks_empty_result_as_non_compliant():
    payload = ""

    result = evaluate_result_compliance(payload)

    assert result["status"] == "non_compliant"
    assert result["severity"] == "critical"
    assert "vide" in " ".join(result["issues"]).lower()


def test_compliance_marks_structured_agent_error_envelope_as_non_compliant():
    payload = {
        "schema_version": 1,
        "command": "Get-PolPassAudit",
        "execution_status": "failed",
        "output_type": "error",
        "output": "",
        "error_message": "SecEdit export failed",
        "empty_reason": None,
    }

    result = evaluate_result_compliance(payload)

    assert result["status"] == "non_compliant"
    assert result["severity"] == "critical"
    assert result["recommendation"] == "SecEdit export failed"


def test_compliance_marks_structured_empty_agent_envelope_as_non_compliant():
    payload = {
        "schema_version": 1,
        "command": "Get-UACAudit",
        "execution_status": "success",
        "output_type": "empty",
        "output": "",
        "error_message": None,
        "empty_reason": "No output captured by the command.",
    }

    result = evaluate_result_compliance(payload)

    assert result["status"] == "non_compliant"
    assert result["severity"] == "critical"
    assert "aucune sortie" in " ".join(result["issues"]).lower() or "vide" in " ".join(result["issues"]).lower()


def test_compliance_detects_windows_defender_exception_in_output_text():
    payload = {
        "schema_version": 1,
        "command": "Get-ASRStatus",
        "execution_status": "success",
        "output_type": "text",
        "output": (
            "Get-MpPreference : L’opération a échoué avec l’erreur suivante:\r\n"
            "0x800106ba\r\n"
            "Au caractère Ligne:8 : 11\r\n"
            "+     $mp = Get-MpPreference\r\n"
            "+           ~~~~~~~~~~~~~~~~\r\n"
            "    + CategoryInfo          : NotSpecified: (MSFT_MpPreference: ... ) [Get-MpPreference], CimException\r\n"
            "    + FullyQualifiedErrorId : HRESULT 0x800106ba,Get-MpPreference"
        ),
        "error_message": None,
        "empty_reason": None,
    }

    result = evaluate_result_compliance(payload)

    assert result["status"] == "non_compliant"
    assert result["severity"] == "critical"
    assert "Get-MpPreference" in " ".join(result["issues"]).lower() or "0x800106ba" in " ".join(result["issues"]).lower()
