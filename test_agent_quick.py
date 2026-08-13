#!/usr/bin/env python3
"""
Script de test rapide pour créer un agent fictif et générer de la data
pour visualiser le dashboard
"""

import requests
import json
import random
from datetime import datetime

BASE_URL = "http://localhost:8000/api"

def enroll_agent():
    """Enregistrer un nouvel agent"""
    random_suffix = random.randint(1000, 9999)
    
    data = {
        "agent_name": f"TEST-PC-AUDIT-{random_suffix}",
        "os_version": "Windows Server 2019",
        "hostname": f"PC-AUDIT-{random_suffix}",
        "username": "AUDIT_SERVICE"
    }
    
    print(f"📝 Enrolling agent: {data['agent_name']}...")
    response = requests.post(f"{BASE_URL}/enroll", json=data)
    
    if response.status_code == 200:
        agent = response.json()
        print(f"✅ Agent enrolled successfully!")
        print(f"   Agent ID: {agent['agent_id']}")
        print(f"   API Key: {agent['api_key'][:20]}...")
        return agent
    else:
        print(f"❌ Failed to enroll agent: {response.status_code}")
        print(f"   {response.text}")
        return None

def send_beacon(agent_id, api_key):
    """Envoyer un beacon (heartbeat)"""
    data = {
        "agent_id": agent_id,
        "api_key": api_key,
        "status": "online",
        "uptime_seconds": 86400,  # 1 jour
        "last_task_id": None
    }
    
    print(f"\n📡 Sending beacon from {agent_id}...")
    response = requests.post(f"{BASE_URL}/beacon", json=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Beacon sent successfully!")
        print(f"   Tasks assigned: {len(result['tasks'])}")
        return True
    else:
        print(f"❌ Beacon failed: {response.status_code}")
        print(f"   {response.text}")
        return False

def create_task(agent_id):
    """Créer une tâche pour l'agent (endpoint de gestion)"""
    data = {
        "command": "Get-Service",
        "parameters": {"status": "running"},
        "priority": 1
    }
    
    print(f"\n📋 Creating task for {agent_id}...")
    response = requests.post(f"{BASE_URL}/tasks/{agent_id}", json=data)
    
    if response.status_code == 200:
        task = response.json()
        print(f"✅ Task created successfully!")
        print(f"   Task ID: {task['task_id']}")
        return task['task_id']
    else:
        print(f"❌ Task creation failed: {response.status_code}")
        print(f"   {response.text}")
        return None

def submit_result(agent_id, api_key, task_id):
    """Soumettre un résultat d'audit"""
    # Simulation de vraies sorties PowerShell (texte brut)
    powershell_output = """
Status   Name               DisplayName
------   ----               -----------
Running  ADWS               Active Directory Web Services
Running  AppHostSvc         Application Host Helper Service
Running  AudioEndpointBu... Windows Audio Endpoint Builder
Running  AudioSrv           Windows Audio
Running  AxInstSrv          ActiveX Installer (AxInstSrv)
Running  BFE                Base Filtering Engine
Running  BITS               Background Intelligent Transfer Servi
Running  COMSysApp          COM+ System Application
Running  CoreMessaging      CoreMessaging
Running  CryptSvc           Cryptographic Services
Running  CscService         Offline Files
Running  DcomLaunch         DCOM Server Process Launcher
Running  Dhcp               DHCP Client
Running  DiagTrack          DiagTrack
Running  DmEnrollmentSvc... Device Management Enrollment Service
Running  Dnscache           DNS Client
Running  Eaphost            Extensible Authentication Protocol
Running  EventLog           Windows Event Log
Running  EventSystem        COM+ Event System
Running  Fax                Fax
Running  fhsvc              File History Service
Running  FontCache          Windows Font Cache Service
Running  fsysagent          Microsoft Filesystem Agent
Running  gpsvc              Group Policy Client
Running  hidserv            Human Interface Device Access
Running  IKEEXT             IKE and AuthIP IPsec Keying Modules
Running  iphlpsvc           IP Helper
Running  IISADMIN           IIS Admin Service
Running  kdc                Kerberos Key Distribution Center
Running  KeyIso             CNG Key Isolation
Running  KtmRm              KtmRm for Distributed Transaction Coord
Running  LanmanServer       Server
Running  LanmanWorkstation  Workstation
Running  lltdsvc            Link-Layer Topology Discovery Mapper
Running  lmhosts            TCP/IP NetBIOS Helper
Running  LSM                Local Session Manager
Running  MSMQ               Message Queuing
Running  MSiSCSI            iSCSI Initiator Service
Running  msiserver          Windows Installer
Running  napagent           Network Access Protection Agent
Running  NetLogon           Netlogon
Running  Netman             Network Connections
Running  netprofm           Network List Service
Running  NetTcpPortSharing  Net.Tcp Port Sharing Service
Running  nsi                Network Store Interface Service
Running  NtLmSsp            NT LM Security Support Provider
Running  NVSvc              NVIDIA Display Driver Service
Running  ose                Office Source Engine
Running  PeerDistSvc        BranchCache
Running  PerfHost           Performance Counter DLL Host
Running  PlugPlay           Plug and Play
Running  PolicyAgent        IPsec Policy Agent
Running  ProfSvc            User Profile Service
Running  RASAuto            Remote Access Auto Connection Manager
Running  RasSstp            Secure Socket Tunneling Protocol Servi
Running  RemoteAccess       Routing and Remote Access
Running  RemoteRegistry     Remote Registry
Running  RpcEptMapper       RPC Endpoint Mapper
Running  RpcSs              Remote Procedure Call (RPC)
Running  RSoPProv           Resultant Set of Policy Provider
Running  RSVP               QoS RSVP
Running  SACSVR             Special Administration Console Helper
Running  SamSs              Security Accounts Manager
Running  SCardSvr           Smart Card
Running  ScDeviceEnum       Smart Card Device Enumeration Service
Running  Schedule           Task Scheduler
Running  SCPolicySvc        Smart Card PnP Notifier
Running  SensorService     Sensor Service
Running  SensorDataService  Sensor Data Service
Running  SessionEnv         Remote Desktop Configuration
Running  SharedAccess       Internet Connection Sharing (ICS)
Running  sharedaccess       Internet Connection Sharing
Running  ShellHWDetection   Shell Hardware Detection
Running  SldpGateway        Bluetooth Audio Gateway Service
Running  Spooler            Print Spooler
Running  SPP                Software Protection
Running  sppuinotify        SPP Notification Service
Running  SstpSvc            Secure Socket Tunneling Protocol
Running  stisvc             Windows Image Acquisition (WIA)
Running  swprv              Shadow Copy Provider
Running  SysmonOperational  Operational
Running  SystemEventsBroker System Events Broker
Running  TapiSrv            Telephony
Running  TermService        Remote Desktop Services
Running  Themes             Themes
Running  THREADORDER        Thread Ordering Server
Running  TpmScaling         Trusted Platform Module Scaling
Running  TrkSvr             Distributed Link Tracking Server
Running  TrkWks             Distributed Link Tracking Client
Running  TrustedInstaller   Windows Modules Installer
Running  UI0Detect          Interactive Services Detection
Running  UmRdpService       Remote Desktop Services UserMode Port Redirector
Running  upnphost           UPnP Device Host
Running  UxSms              UX Shared Manager Service
Running  USBHUB             USB Hub Service
Running  VaultSvc          Vault
Running  vds                Virtual Disk Service
Running  VSS                Volume Shadow Copy
Running  W3SVC              World Wide Web Publishing Service
Running  WaaSMedicSvc       Windows Update Medic Service
Running  WalletService      Wallet Service
Running  WbioSrvc           Windows Biometric Service
Running  WcsPlugInService   Windows Color System
Running  WdBoot             WD Boot
Running  WebClient          WebClient
Running  Wecsvc             Windows Event Collector
Running  wercplsupport      Problem Reports and Solutions Control Panel Support
Running  WerSvc             Windows Error Reporting Service
Running  WesApmService      Windows Event Analysis And Performance Monitoring Service
Running  WiaRpc             Windows Image Acquisition (WIA) Remote Protocol
Running  WinDefend          Windows Defender Antimalware Service
Running  WinHttpAutoProxy...  WinHTTP Web Proxy Auto-Discovery Servi
Running  Winmgmt            Windows Management Instrumentation
Running  WinRM              Windows Remote Management (WS-Managem...
Running  WinUsb             WinUSB Device Driver
Running  Wlansvc            WLAN AutoConfig
Running  wmiApSrv           WMI Performance Adapter
Running  WMPNetworkSvc      Windows Media Player Network Sharing S
Running  WorkfoldersSvc     Work Folders
Running  WpcMonSvc          Parental Controls
Running  WpnService         Windows Push Notifications System Service
Running  WSearch            Windows Search
Running  wuauserv           Windows Update
Running  XblAuthManager     Xbox Live Authentication Manager
Running  XblGameSave        Xbox Live Game Save
Running  xbgm               Xbox Game Monitoring
Running  XboxNetApiSvc      Xbox Live Networking Service
    """
    
    data = {
        "agent_id": agent_id,
        "api_key": api_key,
        "task_id": task_id,
        "status": "success",
        "result": powershell_output.strip(),  # Texte brut de la sortie
        "execution_time_ms": 1250,
        "error_message": None
    }
    
    print(f"\n✔️ Submitting result for task {task_id}...")
    response = requests.post(f"{BASE_URL}/results", json=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Result submitted successfully!")
        print(f"   Message: {result['message']}")
        return True
    else:
        print(f"❌ Result submission failed: {response.status_code}")
        print(f"   {response.text}")
        return False

def get_system_overview():
    """Récupérer la vue d'ensemble du système"""
    print(f"\n📊 Fetching system overview...")
    response = requests.get(f"{BASE_URL}/monitoring/overview")
    
    if response.status_code == 200:
        overview = response.json()
        print(f"✅ System Overview:")
        print(f"   Total Agents: {overview['agents']['total']}")
        print(f"   Total Tasks: {overview['tasks']['total']}")
        if 'success_rate' in overview:
            print(f"   Success Rate: {overview['success_rate']:.1f}%")
        print(f"\n📊 Full Overview:")
        print(json.dumps(overview, indent=2))
        return True
    else:
        print(f"❌ Failed to fetch overview: {response.status_code}")
        return False

def main():
    print("=" * 60)
    print("🚀 C2 Server API - Quick Test Agent")
    print("=" * 60)
    
    # Step 1: Enroll agent
    agent = enroll_agent()
    if not agent:
        return
    
    agent_id = agent['agent_id']
    api_key = agent['api_key']
    
    # Step 2: Send first beacon (should return 0 tasks)
    if not send_beacon(agent_id, api_key):
        return
    
    # Step 3: Create task
    task_id = create_task(agent_id)
    if not task_id:
        return
    
    # Step 4: Send second beacon (should now return the created task)
    print("\n📡 Sending second beacon to fetch the task...")
    if not send_beacon(agent_id, api_key):
        return
    
    # Step 5: Submit result
    if not submit_result(agent_id, api_key, task_id):
        return
    
    # Step 6: Get overview
    get_system_overview()
    
    print("\n" + "=" * 60)
    print("✨ Test completed successfully!")
    print("✨ Refresh your dashboard at http://localhost:8080 to see the data")
    print("=" * 60)

if __name__ == "__main__":
    main()
