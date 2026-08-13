#!/usr/bin/env python3
"""
Multi-Agent Audit Testing Script
Test the API with multiple concurrent agents
"""

import requests
import json
import time
import random
from datetime import datetime

def test_multi_agents(num_agents=3, server_url="http://localhost:8000", delay_seconds=3):
    """Run multi-agent audit tests"""
    
    print("\n" + "="*60)
    print("  Multi-Agent Audit Testing Suite")
    print("="*60)
    print(f"\nConfiguration:")
    print(f"  - Agents: {num_agents}")
    print(f"  - Server: {server_url}")
    print(f"  - Delay: {delay_seconds} seconds\n")
    
    # Step 1: Register agents
    print("="*60)
    print("[STEP 1] Registering agents...")
    print("="*60)
    
    agents = []
    for i in range(1, num_agents + 1):
        agent_name = f"AUDIT-AGENT-{i}-{random.randint(10000, 99999)}"
        hostname = f"AUDIT-HOST-{i}"
        
        print(f"\n  Agent {i}/{num_agents}: {agent_name}")
        
        try:
            body = {
                "agent_name": agent_name,
                "os_version": "Windows Server 2022",
                "hostname": hostname,
                "username": f"auditor{i}"
            }
            
            resp = requests.post(
                f"{server_url}/api/enroll",
                json=body,
                timeout=5
            )
            
            if resp.status_code == 200:
                data = resp.json()
                agents.append({
                    "id": data["agent_id"],
                    "key": data["api_key"],
                    "name": agent_name,
                    "index": i
                })
                print(f"    [OK] Agent ID: {data['agent_id']}")
                print(f"    [OK] API Key: {data['api_key'][:20]}...")
            else:
                print(f"    [ERROR] Status {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"    [ERROR] {str(e)}")
        
        time.sleep(0.5)
    
    print(f"\n  Result: {len(agents)}/{num_agents} agents registered")
    
    # Step 2: Send beacons
    print("\n" + "="*60)
    print("[STEP 2] Sending beacons...")
    print("="*60)
    
    for agent in agents:
        try:
            body = {
                "agent_id": agent["id"],
                "api_key": agent["key"],
                "status": "healthy",
                "uptime_seconds": random.randint(3600, 86400)
            }
            
            resp = requests.post(
                f"{server_url}/api/beacon",
                json=body,
                timeout=5
            )
            
            if resp.status_code == 200:
                print(f"  [OK] Agent {agent['index']} beacon sent")
            else:
                print(f"  [ERROR] Agent {agent['index']}: {resp.status_code}")
        except Exception as e:
            print(f"  [ERROR] Agent {agent['index']}: {str(e)}")
    
    # Step 3: Create audit tasks and submit results
    print("\n" + "="*60)
    print("[STEP 3] Creating audit tasks...")
    print("="*60)
    
    commands = [
        "Get-Process",
        "Get-Service",
        "Get-LocalUser",
        "Get-NetAdapter",
        "Get-LocalGroup",
        "Get-ChildItem C:\\"
    ]
    
    tasks = []
    for agent in agents:
        command = commands[agent["index"] % len(commands)]
        
        print(f"\n  Agent {agent['index']}: Creating task for {command[:40]}")
        
        try:
            body = {
                "agent_id": agent["id"],
                "command": command,
                "description": f"Execute {command}"
            }
            
            resp = requests.post(
                f"{server_url}/api/tasks/{agent['id']}",
                json=body,
                timeout=5
            )
            
            if resp.status_code == 200:
                data = resp.json()
                task_id = data['task_id']
                tasks.append({
                    "agent_index": agent["index"],
                    "task_id": task_id,
                    "command": command
                })
                print(f"    [OK] Task ID: {task_id}")
            else:
                print(f"    [ERROR] Status {resp.status_code}")
                try:
                    print(f"           {resp.json()}")
                except:
                    pass
        except Exception as e:
            print(f"    [ERROR] {str(e)}")
        
        time.sleep(0.3)
    
    print(f"\n  Created: {len(tasks)} tasks")
    
    # Step 3b: Submit audit results
    print("\n" + "="*60)
    print("[STEP 3b] Submitting audit results...")
    print("="*60)
    
    for i, task in enumerate(tasks):
        agent = agents[i]
        exec_time = random.randint(100, 2000)
        
        print(f"\n  Agent {task['agent_index']}: Submitting result")
        
        try:
            output_data = {
                "result": "simulated_data",
                "timestamp": datetime.now().isoformat()
            }
            
            body = {
                "agent_id": agent["id"],
                "api_key": agent["key"],
                "task_id": task["task_id"],
                "status": "success",
                "result": "Audit completed successfully",
                "output": json.dumps(output_data),
                "execution_time_ms": exec_time
            }
            
            resp = requests.post(
                f"{server_url}/api/results",
                json=body,
                timeout=5
            )
            
            if resp.status_code == 200:
                data = resp.json()
                result_id = data.get('result_id', 'unknown')
                print(f"    [OK] Result ID: {result_id}")
                print(f"    [OK] Execution: {exec_time}ms")
            else:
                print(f"    [ERROR] Status {resp.status_code}")
                try:
                    print(f"           {resp.json()}")
                except:
                    pass
        except Exception as e:
            print(f"    [ERROR] {str(e)}")
        
        time.sleep(0.3)
    
    # Step 4: Wait
    print(f"\n" + "="*60)
    print("[STEP 4] Waiting for processing...")
    print("="*60 + f"\n  Waiting {delay_seconds} seconds...")
    
    for i in range(delay_seconds, 0, -1):
        print(f"  {i}...", end="", flush=True)
        time.sleep(1)
    print("\n  Done!\n")
    
    # Step 5: Get system overview
    print("="*60)
    print("[STEP 5] System Status")
    print("="*60)
    
    try:
        resp = requests.get(f"{server_url}/api/monitoring/overview", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            print(f"\n  System Overview:")
            print(f"    - Total Agents: {data.get('agents', {}).get('total', 'N/A')}")
            active = data.get('agents', {}).get('active', 0)
            if active:
                print(f"    - Active: {active}")
            inactive = data.get('agents', {}).get('inactive', 0)
            if inactive:
                print(f"    - Inactive: {inactive}")
            print(f"    - Total Results: {data.get('results', {}).get('total', 0)}")
            success_rate = data.get('results', {}).get('success_rate', 0)
            if success_rate:
                print(f"    - Success Rate: {success_rate*100:.1f}%")
            avg_time = data.get('execution_time_avg_ms', 'N/A')
            if avg_time != 'N/A':
                print(f"    - Avg Exec Time: {avg_time}ms")
    except Exception as e:
        print(f"  [ERROR] {str(e)}")
    
    # Step 6: Get agents dashboard
    print("\n" + "="*60)
    print("[STEP 6] Agents Dashboard")
    print("="*60)
    
    try:
        resp = requests.get(f"{server_url}/api/monitoring/agents", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            print()
            for agent_data in data.get("agents", []):
                print(f"  Agent: {agent_data['agent_name']}")
                print(f"    - Status: {agent_data['status']}")
                print(f"    - Success Rate: {agent_data['success_rate']}%")
                print()
    except Exception as e:
        print(f"  [ERROR] {str(e)}")
    
    # Step 7: Get results dashboard
    print("="*60)
    print("[STEP 7] Results Dashboard")
    print("="*60)
    
    try:
        resp = requests.get(f"{server_url}/api/monitoring/results", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            print(f"\n  Results Summary:")
            print(f"    - Total: {data.get('total_results', 0)}")
            successful = data.get('successful_results', 0)
            if successful:
                print(f"    - Successful: {successful}")
            failed = data.get('failed_results', 0)
            if failed:
                print(f"    - Failed: {failed}")
            success_rate = data.get('success_rate', 0)
            if success_rate:
                print(f"    - Success Rate: {success_rate*100:.1f}%")
            avg_time = data.get('average_execution_time_ms', 'N/A')
            if avg_time != 'N/A':
                print(f"    - Avg Execution: {avg_time}ms")
    except Exception as e:
        print(f"  [ERROR] {str(e)}")
    
    # Step 8: Get alerts
    print("\n" + "="*60)
    print("[STEP 8] System Alerts")
    print("="*60)
    
    try:
        resp = requests.get(f"{server_url}/api/monitoring/alerts", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            print()
            if not data.get("alerts"):
                print("  [OK] No alerts - System healthy!")
            else:
                for alert in data["alerts"]:
                    print(f"  [{alert['level'].upper()}] {alert['type']}")
            print(f"  Overall: {data['overall_level'].upper()}")
    except Exception as e:
        print(f"  [ERROR] {str(e)}")
    
    # Final summary
    print("\n" + "="*60)
    print("[STEP 9] Final Report")
    print("="*60)
    print(f"\n  Test Summary:")
    print(f"    [OK] Agents registered: {len(agents)}")
    print(f"    [OK] Audit results submitted: {len(agents)}")
    print(f"\n  View results at:")
    print(f"    - Dashboard: http://localhost:8080")
    print(f"    - API Docs: http://localhost:8000/docs")
    
    print("\n" + "="*60)
    print("Test Completed!")
    print("="*60 + "\n")

if __name__ == "__main__":
    import sys
    
    num_agents = 3
    if len(sys.argv) > 1:
        try:
            num_agents = int(sys.argv[1])
        except:
            pass
    
    test_multi_agents(num_agents=num_agents)
